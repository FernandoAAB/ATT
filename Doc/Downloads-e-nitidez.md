# Downloads no ATT e nitidez da interface

## Evidências e limite do diagnóstico

A foto confirma HTTP 404 (`0x80190194`) para o EpsonNet Print. O usuário também
relatou falhas nos demais pacotes, funcionamento no PowerShell e escala de 100%.
Não temos os códigos individuais dessas outras falhas nem o comando usado no
terminal. Portanto, não há evidência para atribuir todas elas ao link da Epson
ou afirmar que o modo silencioso explica cada caso.

O ATT usava exclusivamente `--silent --disable-interactivity`, entrada fechada e
janela oculta. Isso impede responder a solicitações do winget e difere de executar
um comando normal no PowerShell. Agora existe uma alternativa explícita com
janela para testar essa diferença e permitir a interação necessária.

## Usar a alternativa com janela

1. Abra **Configurações** e marque **Usar PowerShell com janela nesta sessão**.
2. Volte às **Atualizações** e clique em **Selecionar falhas**, ou escolha os pacotes.
3. Clique em **Atualizar selecionados** e responda às solicitações no terminal.
4. Se houver falha, leia o retorno e pressione Enter para retornar ao ATT.

A opção não inicia instalações sozinha. É temporária e volta ao padrão na próxima
abertura. O ATT mantém a execução sequencial e registra código, modo, comando e
retorno do winget quando disponível. O terminal usa Windows PowerShell sem perfil, com a mesma conta
e permissões do ATT; não força elevação nem aceita contratos automaticamente.
Entrada e saída permanecem ligadas ao console. Ao terminar, o ATT tenta ler as
últimas 200 linhas do buffer do terminal e incluir o trecho no histórico, limitado
a 12.000 caracteres. Alguns hosts não oferecem leitura do buffer; nesse caso,
os detalhes informam que o texto ficou indisponível e preservam o código de saída.
O texto da coleta passa por um arquivo temporário removido ao concluir a tentativa.
UTF-16 e UTF-8 são aceitos na leitura desse arquivo.

Essa escolha também considera o [Reporter do winget](https://github.com/microsoft/winget-cli/blob/5d302e449b63ca1534bf4b7c871f048ad07d5dca/src/AppInstallerCLICore/ExecutionReporter.cpp):
o construtor verifica `GetConsoleMode` para entrada e saída, e `CanPrompt` usa esse
resultado. Por isso o modo com janela não passa o winget por um pipeline para
capturar a saída. A coleta ocorre depois da conclusão.

Uma falha continua sendo falha, inclusive ao fechar o terminal antes da conclusão.
O resultado segue o código de saída; abrir uma janela não confirma a instalação.
Uma falha não remove os outros pacotes nem cancela a fila.

## Comparar quando o erro persistir

Em **Detalhes**, use **Copiar detalhes** para obter o pacote, origem, código,
comando executado e retorno. A comparação deve usar o mesmo pacote, origem,
conta e nível de permissão. Um PowerShell executado como administrador pode ter
comportamento diferente de um ATT aberto normalmente.

Por exemplo, para um pacote específico:

```powershell
winget --version
winget upgrade --id Mozilla.Firefox --exact --source winget
```

O comando executado pelo modo silencioso acrescenta `--silent --disable-interactivity`.
Não execute vários instaladores simultaneamente para fazer a comparação.
Se o mesmo pacote falhar nos dois modos com 404, o modo com janela não repara o
arquivo ausente. Consulte [o caso EpsonNet Print](EpsonNetPrint-404.md).
Nenhuma origem é redefinida e nenhuma configuração de rede ou verificação de
certificado/integridade é desativada pelo ATT.

## Ícones e desenho

Os ícones anteriores eram traços fracionados de 16 pixels no Canvas, sem
suavização das bordas. As abas agora usam ícones de 20 pixels com maior contraste.
Cada tamanho é renderizado previamente em resolução oito vezes maior e reduzido
uma vez; o programa desenha o PNG resultante no seu tamanho final, sem ampliá-lo.
Busca, atualização e informação também usam as máscaras suavizadas.
O texto das abas passou de 12 para 13 pixels. Cores, navegação e layout foram mantidos.

`att_display.enable_dpi_awareness()` é chamado antes de criar a primeira janela
Tk, solicita a renderização nativa com DPI do sistema e respeita um manifesto já
configurado. Isso evita ampliação por bitmap pelo Windows quando aplicável;
não prova que a escala era a causa do relato em 100%. Não é uma implementação
de redimensionamento automático por monitor. A nitidez de fontes no Windows ainda
depende do Tk, da fonte disponível e da configuração de exibição.

O ATT continua usando apenas a biblioteca padrão. Para regenerar as máscaras em
desenvolvimento, instale Pillow e execute `python tools/build_icons.py` da raiz
do projeto. A geração desta revisão usou Pillow 12.3.0; o usuário do programa não
precisa instalar Pillow. `att_icon_data.py` deve acompanhar os demais módulos.

## Validação

```powershell
python -m unittest -v
```

Os testes simulam o limite externo do Windows/winget: permissões de interação,
pacote exato, rejeição de identificadores inseguros, leitura do erro 404 e código
de saída do terminal. A interface é exercitada com Tk/Xvfb, incluindo uma fila
com falha e sucesso, controles durante a operação, imagens das abas e ordem de
inicialização de DPI. APIs de DPI e processos do Windows são simulados.

As cinco prévias do README foram refeitas com dados de exemplo. Não houve
instalação real neste ambiente Linux; os downloads, as perguntas no terminal e a
nitidez nativa precisam ser confirmados no Windows. O executável antigo não foi
recompilado e não contém estas mudanças.
