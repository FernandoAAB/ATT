# EpsonNet Print — erro de download 404

## Evidência recebida

A imagem do Histórico mostra o pacote EpsonNet Print e este retorno do winget:

```text
Download request status is not success.
0x80190194 : Não encontrado (404).
```

Esse retorno indica que a requisição de download recebeu HTTP 404. A atualização
desse pacote não foi concluída. A mensagem não prova o resultado dos outros
programas que aparecem no Histórico: cada linha precisa de seu próprio resultado.

## Catálogo consultado

O identificador é `EPSON.EpsonNetPrint`, na origem `winget`. O catálogo consultado
lista a versão 3.3.1 e aponta para instaladores em `download.epson-europe.com`:

[Manifesto de instalação do pacote no catálogo Microsoft](https://github.com/microsoft/winget-pkgs/blob/master/manifests/e/EPSON/EpsonNetPrint/3.3.1/EPSON.EpsonNetPrint.installer.yaml).

A consulta ao catálogo foi concluída. O teste direto do download foi bloqueado
pelo proxy deste ambiente; o 403 dessa checagem é do proxy e não confirma uma
resposta do servidor Epson. O 404 recebido no Windows está documentado na imagem.
Não foi possível comparar o endereço completo usado no computador com o catálogo,
pois a URL aparece cortada na foto.

## Próximos passos no Windows

Em um terminal, atualize os metadados da origem:

```powershell
winget source update
```

Depois tente somente esse pacote:

```powershell
winget upgrade --id EPSON.EpsonNetPrint --exact --source winget
```

Se continuar retornando 404, atualizar o painel ou repetir a tentativa não garante
a recuperação do arquivo. O endereço precisa ficar disponível no distribuidor
ou ser corrigido no catálogo. Nesse caso, desmarque o EpsonNet Print para atualizar
os demais pacotes e consulte o suporte oficial Epson para o modelo da impressora.

## Tratamento no ATT

O ATT preserva o resultado como **Falhou** e o código original. A orientação de
HTTP 404 aparece tanto quando `0x80190194` é o código retornado quanto quando
está na mensagem de uma falha de download `0x8A150008`. O texto indica atualizar
o catálogo e a limitação de um link indisponível.

Os testes exercitam os dois retornos com a mensagem mostrada na foto. A alteração
é de diagnóstico; não altera URLs, hashes, certificados, aceitação de termos ou
o resultado real do instalador.
