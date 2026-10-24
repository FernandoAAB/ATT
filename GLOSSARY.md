# ATT — Atualização de aplicativos

Linguagem usada para consultar, escolher e acompanhar atualizações de programas.

## Linguagem

**Pacote**:
Um programa identificado dentro de uma origem. Dois pacotes com o mesmo nome ou identificador podem pertencer a origens diferentes.
_Evitar_: nome do programa como identidade.

**Origem**:
O catálogo no qual um pacote é encontrado e pelo qual sua atualização é solicitada.

**Consulta**:
Uma observação dos pacotes e versões disponíveis em um momento. Não garante que o programa continue instalado quando a execução começar.

**Seleção**:
O conjunto de pacotes que o usuário escolheu para uma futura execução. Filtrar a lista não altera a seleção.

**Fila de atualização**:
A sequência de pacotes de uma execução já iniciada. Alterar filtros ou navegar entre telas não muda essa sequência.

**Tentativa**:
A execução de uma atualização para um pacote da fila, com um resultado próprio.

**Processado**:
Um pacote cuja tentativa terminou, inclusive quando falhou ou não havia atualização aplicável.
_Evitar_: atualizado como sinônimo de processado.

**Atualizado**:
Um pacote cuja tentativa confirmou uma atualização aplicada. Pode exigir reinicialização para concluir a instalação.

**Sem atualização**:
Um pacote encontrado cuja tentativa não tinha atualização aplicável. Um pacote não encontrado é uma falha, não este resultado.

**Falha**:
Uma tentativa que não confirmou atualização nem ausência de atualização aplicável. Inclui um pacote que deixou de ser encontrado após a consulta.

**Parar após este pacote**:
Um pedido para concluir a tentativa em andamento e não iniciar as seguintes. Não desfaz uma atualização nem muda a preferência automática.

**Histórico**:
Os resultados das tentativas registradas pelo ATT para o usuário. O total de atualizados considera os registros retidos, não todas as atualizações realizadas no computador.
