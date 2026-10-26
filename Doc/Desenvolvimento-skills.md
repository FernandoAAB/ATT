# Revisão de desenvolvimento orientada por skills

## Objetivo

Corrigir bugs e melhorar a organização do ATT, mantendo o layout atual, conforme
solicitado. A revisão usa as interfaces já documentadas em [Modelagem](Modelagem.md)
e a linguagem de [GLOSSARY.md](../GLOSSARY.md).

## Referências escolhidas

As skills foram lidas diretamente dos repositórios nos commits abaixo. A seleção
considerou o programa Python/Tkinter e seus problemas observados.

| Repositório e revisão | Skill | Aplicação no ATT |
| --- | --- | --- |
| [mattpocock/skills](https://github.com/mattpocock/skills/tree/5beb35b040e3de97e54fa9e386d7e42d15c295c2) | [codebase-design](https://github.com/mattpocock/skills/blob/5beb35b040e3de97e54fa9e386d7e42d15c295c2/skills/engineering/codebase-design/SKILL.md) | Concentrar gravação atômica e bloqueio no módulo `att_storage`; manter os contratos de preferências e histórico |
| Mesmo repositório | [tdd](https://github.com/mattpocock/skills/blob/5beb35b040e3de97e54fa9e386d7e42d15c295c2/skills/engineering/tdd/SKILL.md) | Reproduzir cada falha, aplicar uma correção e confirmar o resultado |
| [sickn33/agentic-awesome-skills](https://github.com/sickn33/agentic-awesome-skills/tree/e8d346bcb691225fb6ae51a49c353bcedb2ef61d) | [systematic-debugging](https://github.com/sickn33/agentic-awesome-skills/blob/e8d346bcb691225fb6ae51a49c353bcedb2ef61d/skills/systematic-debugging/SKILL.md) | Investigar a perda de registros e o fluxo de estados da central de execução antes de alterar código |
| Mesmo repositório | [python-testing-patterns](https://github.com/sickn33/agentic-awesome-skills/blob/e8d346bcb691225fb6ae51a49c353bcedb2ef61d/skills/python-testing-patterns/SKILL.md) | Usar diretórios temporários reais, escritores concorrentes e eventos de interface na suíte `unittest` existente |
| Mesmo repositório | [code-review-checklist](https://github.com/sickn33/agentic-awesome-skills/blob/e8d346bcb691225fb6ae51a49c353bcedb2ef61d/skills/code-review-checklist/SKILL.md) | Conferir comportamento, falhas de I/O, compatibilidade, testes e documentação antes de publicar |

## Bugs reproduzidos

| Situação | Evidência antes da correção | Resultado esperado e verificado |
| --- | --- | --- |
| Duas janelas registrando atualizações | O segundo escritor apagava o registro do primeiro | Ambos os resultados permanecem após reabrir o histórico |
| Oito escritores de histórico simultâneos | Colisões em `history.tmp`, incluindo `FileNotFoundError` | Oito resultados distintos são gravados sem colisão |
| Oito salvamentos de preferência simultâneos | Colisões em `config.tmp`, incluindo `FileNotFoundError` | Todos terminam e a configuração final continua válida |
| Retomada após erro de disco | O resultado pendente reaparecia fora da ordem das tentativas | A retomada preserva os resultados de outra janela, ordena pelo horário e não duplica eventos |
| Fila concluída | O primeiro programa voltava a “Pronto para iniciar” | Resultados reais permanecem visíveis e a execução aparece como concluída |
| Nova seleção após uma atualização | A próxima fila herdava 100% da anterior | A nova seleção aparece em espera, com progresso zero |
| Seleção de atualizações enquanto o inventário estava aberto | A seleção da lista de aplicativos era apagada | A seleção permanece enquanto o inventário e o filtro não mudam |

Cada linha acima foi reproduzida por um teste falhando antes da respectiva correção.

## Organização e persistência

- `att_storage` oferece gravação JSON atômica em temporário exclusivo e bloqueio entre janelas. Usa somente a biblioteca padrão.
- `ActivityStore` relê o arquivo durante a gravação protegida, combina resultados pendentes e retém os 1.000 mais recentes. Os registros novos recebem uma identidade própria; o formato anterior permanece legível.
- Resultados ainda não gravados permanecem na memória para uma nova tentativa quando houver outra gravação ou verificação. Ao fechar a janela, dados que continuam sem gravação podem ser perdidos; o painel apresenta o erro de persistência.
- `history.lock` permanece na pasta de dados. Sua existência não significa que está ocupado: o bloqueio é mantido pelo sistema operacional e liberado ao fechar o arquivo. Não é necessário apagá-lo.
- `Dashboard._render_execution` reúne as regras de apresentação da fila. O inventário é reconstruído apenas quando seus dados, o filtro ou sua mensagem mudam.
- A validação também cobre uma verificação feita por outra janela e um histórico corrompido após a abertura. O arquivo danificado é preservado.

## Validação e limites

```powershell
python -m unittest -v
```

Somente os novos cenários:

```powershell
python -m unittest -v test_revision
```

Os testes usam arquivos temporários, oito escritores concorrentes, dois processos
separados e Tkinter/Xvfb.
A suíte anterior também permanece em execução. Os adaptadores do winget são
simulados, portanto nenhum programa é instalado pelos testes.

O bloqueio usa `msvcrt` no Windows e `fcntl` no Linux. A validação executada neste
ambiente exercita o caminho Linux; a execução nativa no Windows, o comportamento
de permissões e as instalações reais seguem exigindo validação nessa plataforma.
O executável antigo não foi reconstruído nesta revisão.

A revisão posterior de downloads e nitidez segue o mesmo fluxo de diagnóstico e
testes. As evidências, o modo PowerShell com console real, os ícones suavizados e
os limites da validação estão em [Downloads e nitidez](Downloads-e-nitidez.md).
