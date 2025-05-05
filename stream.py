import os
import threading
from typing import Optional, Callable, Dict, ClassVar, Literal
from functools import wraps
from pathlib import Path
from dotenv import load_dotenv
from httpx import request
import logging

logging.getLogger("httpx").setLevel(logging.NOTSET) # Suprime os logs do httpx

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class LogFileHandler(FileSystemEventHandler):
    """Classe para monitorar o arquivo de log e enviar os logs para o LogStream API"""
    def __init__(self, log_file, callback):
        self.log_file = log_file
        self.callback = callback
        self._last_position = 0

    def on_modified(self, event):
        """Evento que é chamado quando o arquivo de log é modificado"""
        if event.src_path == str(self.log_file):
            with open(self.log_file, 'r', encoding='utf-8') as f:
                f.seek(self._last_position)
                new_lines = f.readlines()
                self._last_position = f.tell()
                for line in new_lines:
                    line = line.strip()
                    if line:
                        self.callback(line)

class Config:
    """Configurações do LogStream"""
    
    ConfigKeys = Literal["AUTOMATION_ID", "AUTOMATION_NAME", "LOG_FILE"]
    """Tipagem para as chaves do arquivo de configuração"""

    _project_path: Path = Path.cwd() # Sempre será o diretório do projeto

    _observer: ClassVar[Optional[Observer]] = None
    _handler: ClassVar[Optional[LogFileHandler]] = None

    _api_url: ClassVar[str] = "https://dclick-logstream.insidev.com.br"
    _env_file_name: ClassVar[str] = ".logstream"
    _log_file: ClassVar[Path] = _project_path / ".log"
    _automation_id: ClassVar[Optional[str]]
    _automation_name: ClassVar[Optional[str]]
    _env_file: ClassVar[Path] = _project_path / _env_file_name

    _default_env_config: ClassVar[Dict[str, str]] = {
        "AUTOMATION_ID": "",
        "AUTOMATION_NAME": "",
        "LOG_FILE": str(_project_path / _log_file)
    }

    def __init_subclass__(cls) -> None:
        """Inicializa a configuração quando a classe é herdada."""
        cls._ensure_config()

    @classmethod
    def _ensure_config(cls) -> None:
        """Verifica e cria o arquivo de configuração se necessário."""
        if not cls._env_file.exists():
            with open(cls._env_file, "w") as f:
                for key, value in cls._default_env_config.items():
                    f.write(f"{key}={value}\n")
            print(f"Arquivo .logstream criado em: {cls._env_file}")
        
        load_dotenv(cls._env_file, override=True)
        
        current_automation_id = cls.get_config("AUTOMATION_ID")
        current_automation_name = cls.get_config("AUTOMATION_NAME")

        cls._automation_id = current_automation_id
        cls._automation_name = current_automation_name

        assert None not in (current_automation_id, current_automation_name), "Para usar o LogStream, insira o ID e o nome da automação no arquivo de configuração."
        
    @classmethod
    def get_config(cls, key: ConfigKeys) -> Optional[str]:
        """Retorna as configurações do arquivo de configuração."""
        if key not in cls._default_env_config:
            raise ValueError(f"Chave inválida: {key}")
        
        value = os.getenv(key, cls._default_env_config[key])
        return value if value != "" else None
            
class LogStream(Config):
    """Classe de streaming de logs para o LogStream API."""

    @classmethod
    def send_log(cls, log_content: str) -> Dict[str, str]:
        """Monitora e faz o envio do log para o LogStream API"""
        params = {
            "log_content": log_content,
            "automation_id": cls._automation_id
        }
        request(method="POST", url=f"{cls._api_url}/logs/{cls._automation_id}", params=params)

    @classmethod
    def clear_buffer(cls) -> Dict[str, str]:
        """Limpa o buffer inicial."""
        request(method="POST", url=f"{cls._api_url}/logs/{cls._automation_id}/clear")

    _check_interval: ClassVar[float] = 0.1
    _is_running: ClassVar[bool] = False
    _thread: ClassVar[Optional[threading.Thread]] = None
    _last_position: ClassVar[int] = 0

    @classmethod
    def start(cls) -> None:
        """Inicia o streaming de logs em uma thread separada."""
        if not os.path.exists(cls._log_file):
            raise FileNotFoundError(f"Arquivo de log não encontrado: {cls._log_file}")

        # Limpa o buffer inicial
        cls.clear_buffer()

        def send(line):
            try:
                cls.send_log(log_content=line)
            except Exception as e:
                print(f"Erro ao enviar log: {e}")

        cls._handler = LogFileHandler(cls._log_file, send)
        cls._observer = Observer()
        cls._observer.schedule(cls._handler, path=str(Path(cls._log_file).parent), recursive=False)
        cls._observer.start()
        cls._is_running = True

    @classmethod
    def stop(cls) -> None:
        """Interrompe o streaming de logs"""
        cls._is_running = False
        if cls._observer:
            cls._observer.stop()
            cls._observer.join()
            cls._observer = None
            cls._handler = None

    @classmethod
    def __call__(cls, func: Callable) -> Callable:
        """
        Decorador que gerencia o ciclo de vida do streaming de logs.
        
        Args:
            func (Callable): Função a ser decorada
            
        Returns:
            Callable: Função decorada
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            cls.start()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                cls.stop()
        return wrapper
    
__all__ = ["LogStream"]