# ATT — Central de atualizações para Windows

Painel em Python/Tkinter para gerenciar as atualizações dos programas instalados
pelo `winget`, com seleção manual e atualização automática opcional.

## Imagens do programa

### Painel principal

![Painel principal do ATT](https://raw.githubusercontent.com/FernandoAAB/ATT/main/Doc/Previa-painel.png?v=e7d5bacbce55)

### Histórico de atualizações

![Histórico de atualizações do ATT](https://raw.githubusercontent.com/FernandoAAB/ATT/main/Doc/Previa-historico.png?v=882f70561db8)

### Aplicativos instalados

![Lista de aplicativos instalados no ATT](https://raw.githubusercontent.com/FernandoAAB/ATT/main/Doc/Previa-aplicativos.png?v=02b80fcfdd9d)

Layout de 1280 × 720 baseado na referência visual, com painéis e botões arredondados e ícones suavizados. As capturas usam dados de exemplo
em uma tela virtual Linux; fontes e elementos nativos podem variar no Windows.

### Falhas preservadas na lista

![Resultado de atualização e falha no ATT](https://raw.githubusercontent.com/FernandoAAB/ATT/main/Doc/Previa-falhas.png?v=d278d00912fa)

### Textos acessíveis em janela menor

![Configurações do ATT com rolagem](https://raw.githubusercontent.com/FernandoAAB/ATT/main/Doc/Previa-configuracoes.png?v=288fdd696760)

## Requisitos e execução

- Windows 10/11 com uma versão atual do **App Installer**, que fornece o `winget`.
- Python 3.9 ou posterior com Tkinter (incluído no instalador oficial para Windows).
- Acesso às origens e aos servidores de download dos programas.

Na pasta do projeto, execute:

```powershell
python main.py
```

Não há dependências para instalar com pip. Mantenha todos os módulos `att_*.py`
junto ao `main.py`, incluindo `att_display.py`, `att_icons.py` e `att_icon_data.py`.
O arquivo `Atualizador.exe` incluído no repositório é a versão anterior;
**ele não contém este novo painel**. Use o código Python até que um novo executável
seja gerado no Windows.

## Seções do painel

- **Visão geral:** inventário detectado, atualizações elegíveis, atualizações registradas pelo ATT e horário da última consulta bem-sucedida.
- **Atualizações:** lista de pacotes com busca por nome ou identificador, filtro de tipo e ordenação; a seção Atualizações também permite filtrar por origem e status.
- **Histórico:** registros de execução por usuário, com data, versões, resultado e detalhes do instalador ao selecionar uma linha.
- **Aplicativos:** inventário da última consulta `winget list`, com busca por nome ou identificador.
- **Automação:** preferência para atualizar todos os pendentes na próxima abertura.
- **Configurações:** modo de instalação com janela do PowerShell, localização dos dados e informações sobre o funcionamento.

O número de instalados representa os aplicativos detectados pelo winget, não todos
os componentes do Windows. Um inventário que falhou aparece como indisponível,
sem impedir a atualização dos pacotes já consultados. O contador “Atualizados pelo
ATT” considera resultados de atualização bem-sucedidos nos registros retidos,
incluindo aqueles que precisam de reinicialização. Não é um total de programas
atualizados por outras ferramentas. Datas e horários seguem o relógio local do Windows.

O winget não fornece uma classificação de recomendações ou categorias de software
para esta lista. O filtro de tipo reconhece navegadores, editor, compactador e reprodutor a partir de identificadores conhecidos; os demais aparecem como Outros. Não são atribuídas recomendações de segurança. O ATT não monitora
antivírus nem o estado da proteção do Windows.

## Selecionar e executar

A consulta inicia ao abrir. No modo manual, os pacotes começam desmarcados.
Clique em `[ ]` ou use Espaço na linha para marcar um programa.
**Selecionar todos** inclui todos os pacotes elegíveis, inclusive os ocultos pelos
filtros. Quando todos estão marcados, o botão passa a **Limpar seleção**. A caixa
do cabeçalho também alterna essas duas ações. O filtro **Selecionados** preserva
os resultados da última execução até que a seleção seja modificada. Ao verificar
novamente, esse filtro volta a **Todos os status** para mostrar a nova consulta.

**Atualizar N selecionados** inicia a fila em sequência. A central de execução
mostra os programas, seus estados e o progresso por quantidade de pacotes
processados; não é o percentual de download de um instalador. Em janelas pequenas,
o resumo do progresso aparece nas opções de execução.
Uma falha não impede a tentativa dos próximos pacotes. Ao concluir, use
**Verificar atualizações** para obter uma nova consulta e atualizar o inventário.
Aplicativos e versões são fotografias da consulta, não um monitoramento contínuo.

Clique no ícone de informação da linha ou pressione Enter na linha para abrir os detalhes do pacote. Uma consulta que falhou permite abrir os detalhes clicando na mensagem central da tabela. Os resultados completos
retidos podem ser consultados no Histórico. A janela de detalhes tem rolagem e
o botão **Copiar detalhes**. **Selecionar falhas** marca apenas os pacotes que
falharam; clique em **Atualizar selecionados** para repetir somente essas tentativas. Não há busca nem instalação de
programas novos nesta versão.

## Automação e interrupção

**Atualizar ao abrir o ATT** começa desativada. A preferência é salva em
`%LOCALAPPDATA%\ATT\config.json` e vale para a próxima abertura. Quando ativa,
atualiza todos os pendentes elegíveis e mantém o painel visível. A opção não
adiciona o ATT à inicialização do Windows.

**Parar após este pacote** só fica disponível durante a atualização. O instalador
atual conclui e os próximos pacotes não são iniciados. A preferência automática
permanece independente dessa parada. Fechar a janela durante uma operação permite
permanecer nela ou sair após a operação atual. Instaladores não são encerrados à força.

## Histórico e erros

O arquivo `%LOCALAPPDATA%\ATT\history.json` guarda a última verificação e até
1.000 resultados, incluindo falhas e detalhes do winget. Ele é separado das
preferências e permanece entre aberturas. Um arquivo de histórico inválido é
preservado, e o painel avisa que não conseguiu carregar/salvar os registros.
Uma falha de gravação não muda o resultado informado pelo instalador.
As gravações do histórico são coordenadas entre janelas e preservam os resultados
de cada uma. Registros pendentes após um erro são tentados novamente na próxima
gravação ou verificação, enquanto a janela continuar aberta. O arquivo
`history.lock` na mesma pasta é usado nessa coordenação e pode permanecer lá.

O painel não exige execução como administrador; instaladores podem solicitar
permissão pelo Windows. A instalação usa o modo silencioso por padrão. Se o pacote
funciona no PowerShell e falha no ATT, abra **Configurações** e marque
**Usar PowerShell com janela nesta sessão**. Volte a **Atualizações**, clique em
**Selecionar falhas** e depois em **Atualizar selecionados**. Cada pacote abre um
terminal com entrada disponível, sem forçar o modo silencioso; responda às
solicitações ali. Em caso de falha, pressione Enter no terminal para retornar ao
ATT. A fila aguarda o término do processo, mantém os resultados e respeita
**Parar após este pacote**. O modo volta ao padrão ao reabrir o programa.

Contratos não são aceitos automaticamente em nenhum dos modos. Os detalhes
preservam o código, o modo, o comando executado e um comando para comparação.
No modo silencioso, também incluem a saída original; com janela, tentam obter o
trecho final do console e avisam quando o host não disponibiliza esse texto.
Há orientações para erros conhecidos de download e instalador
ocupado. Consulte [Menus e falhas](Doc/Menus-e-falhas.md) para os casos corrigidos.
O modo com janela permite testar a diferença de interação; não garante corrigir
erros de rede ou links indisponíveis. Veja [Downloads e nitidez](Doc/Downloads-e-nitidez.md).

Para o erro **EpsonNet Print — HTTP 404 (`0x80190194`)**, consulte
[o diagnóstico e os comandos para atualizar o catálogo](Doc/EpsonNetPrint-404.md).

A leitura depende da tabela de saída do winget. Formatos não reconhecidos geram
erro; identificadores truncados ou ambíguos são bloqueados para atualização.
O ATT informa quando uma instalação exige reinicialização, sem reiniciar o computador.

## Testes

As definições do domínio estão em [GLOSSARY.md](GLOSSARY.md). A revisão baseada em
`mattpocock/skills`, os contratos exercitados e os cenários de estresse estão em
[Modelagem e cenários de estresse](Doc/Modelagem.md).
A seleção de skills dos dois repositórios, os bugs reproduzidos e as mudanças de
organização estão em [Revisão de desenvolvimento](Doc/Desenvolvimento-skills.md).

```powershell
python -m unittest -v
```

A suíte usa respostas simuladas e não instala programas. Cobre tabelas do winget,
inventário, seleção, filtros, navegação, filas, persistência, falhas e interrupção.
Também verifica o encaminhamento ao PowerShell, a captura de erro no terminal,
a configuração de DPI antes do Tk e a permanência dos ícones após navegar.
Testes de interface precisam de uma tela; em Linux podem usar Xvfb. Sem tela,
esses testes são explicitamente ignorados. Instalações reais, permissões e
compatibilidade com o winget instalado precisam ser verificadas no Windows.
