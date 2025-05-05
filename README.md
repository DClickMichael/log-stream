# LogStream

LogStream é uma ferramenta que monitora e transmite arquivos de log em tempo real para uma API WebSocket.

## Instalação
```
pip install https://github.com/DClickMichael/log-stream/releases/download/v1.0.2/dclick_log_stream-1.0.2-py3-none-any.whl
```

## Configuração

Antes de usar o LogStream, configure o arquivo `.logstream` no diretório raiz do seu projeto. Este arquivo deve conter as seguintes variáveis:

```env
AUTOMATION_ID=id_automacao
AUTOMATION_NAME=nome_automacao
LOG_FILE=caminho\.log
```

## Uso Básico

O LogStream fornece um decorador que gerencia automaticamente o ciclo de vida do monitoramento de logs. Aqui está um exemplo básico de uso:

```python
from logstream import LogStream

@LogStream()
def sua_funcao():
    # Os logs serão automaticamente monitorados e enviados para a API enquanto a função decorada está em execução
    pass
```

## Como Funciona

1. O decorador `@LogStream()` inicia automaticamente o monitoramento do arquivo de log quando a função decorada é chamada
2. Durante a execução da função, qualquer nova linha adicionada ao arquivo de log será transmitida para a API
3. Quando a função termina, o monitoramento é automaticamente interrompido


## Observações

- O arquivo de log especificado em `LOG_FILE` deve existir antes de iniciar o monitoramento
- O monitoramento é feito em uma thread separada, não interferindo na execução principal do seu código
- Em caso de erro no envio de logs, o erro será impresso no console, mas não interromperá a execução da automação
