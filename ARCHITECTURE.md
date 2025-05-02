# Documentação Visual do Projeto

Este documento apresenta uma visão geral dos principais componentes e fluxos de dados do projeto "Zendesk - Glean - Answers".

```mermaid
flowchart TD
    subgraph Ambiente
        ENV[.env / Variáveis de Ambiente]
    end

    subgraph Configuracao["Configuração"]
        CFG[config.py]
    end

    ENV --> CFG

    subgraph ScriptsExportacao["Scripts de Exportação"]
        ET[exportar-zendesk-ticketsinfo.py]
    end

    subgraph Webhooks
        WE1[webhook-com-excel.py]
        WE2[webhook-com-txt-estruturado.py]
        WE3[webhook-txt-estruturado-com-email.py]
        WF[teste-flask.py]
    end

    subgraph InteracoesGlean["Interações com Glean"]
        TG[teste-glean.py]
        TT[trackingtoken.py]
        GC[gleancall.py]
        WEG["[V1] - webhook-enviando-glean.py"]
    end

    subgraph PostagemEmTicket["Postagem em Ticket"]
        PT["[V1] - post-ticket-zendesk.py"]
    end

    CFG --> ET
    CFG --> WE1
    CFG --> WE2
    CFG --> WE3
    CFG --> WF
    CFG --> TG
    CFG --> TT
    CFG --> GC
    CFG --> WEG
    CFG --> PT

    subgraph ZendeskAPI["Zendesk API"]
        ZD[Zendesk API]
    end

    subgraph GleanAPI["Glean API"]
        GL[Glean API]
    end

    ET -->|GET Tickets| ZD
    WE1 -->|Recebe Webhook| WF
    WF -->|Chama GET Ticket e Comments| ZD
    WE2 -->|Recebe Webhook| WF
    WE3 -->|Recebe Webhook| WF

    WEG -->|Recebe Webhook| WF
    WEG -->|GET Ticket & Comments| ZD
    WEG -->|Gera texto do ticket| WEG
    WEG -->|Envia para Glean| GL

    PT -->|PUT Update Ticket| ZD
    TG -->|POST Chat| GL
    TT -->|POST Chat/Feedback| GL
    GC -->|POST Feedback| GL
```

Legenda:
- **.env / Variáveis de Ambiente**: arquivo que define credenciais e endpoints.
- **config.py**: módulo que centraliza o carregamento de configurações.
- **exportar-zendesk-ticketsinfo.py**: script de exemplo para exportar comentários de ticket para Excel.
- **Webhooks**: scripts Flask que recebem eventos do Zendesk e salvam dados em Excel/TXT.
- **Interações com Glean**: exemplos de envio de mensagens, obtenção de tokens e feedback.
- **Postagem em Ticket**: script para atualizar tickets via API do Zendesk.
- **Zendesk API** e **Glean API**: serviços externos consumidos pelos scripts.