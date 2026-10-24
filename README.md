# ATT — Central de atualizações para Windows

Painel em Python/Tkinter para gerenciar as atualizações dos programas instalados
pelo `winget`, com seleção manual e atualização automática opcional.

## Imagens do programa

### Painel principal

![Painel principal do ATT](https://raw.githubusercontent.com/FernandoAAB/ATT/main/Doc/Previa-painel.png)

### Histórico de atualizações

![Histórico de atualizações do ATT](https://raw.githubusercontent.com/FernandoAAB/ATT/main/Doc/Previa-historico.png)

### Aplicativos instalados

![Lista de aplicativos instalados no ATT](https://raw.githubusercontent.com/FernandoAAB/ATT/main/Doc/Previa-aplicativos.png)

Layout de 1280 × 720 baseado na referência visual, com painéis, botões e tabela vetoriais arredondados. As capturas usam dados de exemplo
em uma tela virtual Linux; fontes e elementos nativos podem variar no Windows.

## Requisitos e execução

- Windows 10/11 com uma versão atual do **App Installer**, que fornece o `winget`.
- Python 3.9 ou posterior com Tkinter (incluído no instalador oficial para Windows).
- Acesso às origens e aos servidores de download dos programas.

Na pasta do projeto, execute:

```powershell
python main.py
```

Não há dependências para instalar com pip. Mantenha os módulos `att_backend.py`,
`att_dashboard.py`, `att_widgets.py` e `att_history.py` junto ao `main.py`.
O arquivo `Atualizador.exe` incluído no repositório é a versão anterior;
**ele não contém este novo painel**. Use o código Python até que um novo executável
seja gerado no Windows.

## Seções do painel

- **Visão geral:** inventário detectado, atualizações elegíveis, atualizações registradas pelo ATT e horário da última consulta bem-sucedida.
- **Atualizações:** lista de pacotes com busca por nome ou identificador, filtro de tipo e ordenação; a seção Atualizações também permite filtrar por origem e status.
- **Histórico:** registros de execução por usuário, com data, versões, resultado e detalhes do instalador ao selecionar uma linha.
- **Aplicativos:** inventário da última consulta `winget list`, com busca por nome ou identificador.
- **Automação:** preferência para atualizar todos os pendentes na próxima abertura.
- **Configurações:** localização dos dados e informações sobre o funcionamento.

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
do cabeçalho também alterna essas duas ações.

**Atualizar N selecionados** inicia a fila em sequência. A central de execução
mostra os programas, seus estados e o progresso por quantidade de pacotes
processados; não é o percentual de download de um instalador. Em janelas pequenas,
o resumo do progresso aparece nas opções de execução.
Uma falha não impede a tentativa dos próximos pacotes. Ao concluir, use
**Verificar atualizações** para obter uma nova consulta e atualizar o inventário.
Aplicativos e versões são fotografias da consulta, não um monitoramento contínuo.

Clique no ícone de informação da linha ou pressione Enter na linha para abrir os detalhes do pacote. Uma consulta que falhou permite abrir os detalhes clicando na mensagem central da tabela. Os resultados completos
retidos podem ser consultados no Histórico. Não há busca nem instalação de
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

O painel não exige execução como administrador; instaladores podem solicitar
permissão pelo Windows. A instalação é silenciosa, e contratos não são aceitos
automaticamente. Para exigências de interação, contratos ou problemas nas origens,
revise os detalhes e execute `winget upgrade` em um terminal para resolver as
solicitações apresentadas pelo próprio winget.

A leitura depende da tabela de saída do winget. Formatos não reconhecidos geram
erro; identificadores truncados ou ambíguos são bloqueados para atualização.
O ATT informa quando uma instalação exige reinicialização, sem reiniciar o computador.

## Testes

As definições do domínio estão em [GLOSSARY.md](GLOSSARY.md). A revisão baseada em
`mattpocock/skills`, os contratos exercitados e os cenários de estresse estão em
[Modelagem e cenários de estresse](Doc/Modelagem.md).

```powershell
python -m unittest -v
```

A suíte usa respostas simuladas e não instala programas. Cobre tabelas do winget,
inventário, seleção, filtros, navegação, filas, persistência, falhas e interrupção.
Testes de interface precisam de uma tela; em Linux podem usar Xvfb. Sem tela,
esses testes são explicitamente ignorados. Instalações reais, permissões e
compatibilidade com o winget instalado precisam ser verificadas no Windows.
