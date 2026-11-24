# 2. A viagem de uma linha 🚂

Considere `Quant. CI = 001`, ano 2026, setor Administrativo.

1. A CLI informa arquivo, aba e ano. O ano é um parâmetro de negócio: uma célula
   decorativa com “ANO 2025” não muda a identidade da ficha.
2. A leitura preserva `001` se estiver armazenado como texto. Um número Excel com
   máscara visual `000` continua sendo o número `1`: formatação não é conteúdo.
3. O cabeçalho ganha nomes canônicos. “Quant.  CI” vira `quant_ci`.
4. A linha física original é registrada, inclusive se houver linhas vazias no meio.
5. A qualidade exige chave preenchida e única dentro do arquivo, layout homologado
   e pelo menos um registro. Se uma regra falha, o lote inteiro é bloqueado.
6. O repositório compara a ficha com `(2026, 001)` no banco.
7. Se mudou o setor, atualiza o estado vigente e grava uma nova versão em JSON.
   Se nada mudou, contabiliza a reexecução sem gerar outra versão.
8. O painel consulta a view, enquanto o histórico permite ver os estados anteriores.

## O crachá da ficha: chave natural

`(ano_origem, quant_ci)` diferencia a CI 001 de 2025 da CI 001 de 2026.
Essa chave precisa ser estável. Se a empresa renumerar uma CI, ela aparecerá como
outro projeto. Antes de produção, confirme essa hipótese com quem mantém as planilhas.
Identificadores `1`, `1.0` e `001` são textos diferentes: não os fundimos sem regra.

## O cadeado: integridade e concorrência

A unicidade é garantida por um índice único no banco. A aplicação também obtém um
bloqueio transacional por ano, de modo que duas execuções do ETL para o mesmo ano
não comparem simultaneamente estados antigos. Anos diferentes podem seguir juntos.
Escritas externas que não respeitem esse protocolo devem ser evitadas por permissões.

Atualização, versão e conclusão da auditoria participam da mesma transação.
Se a terceira ficha falhar depois de duas inserções, todas são desfeitas, inclusive
as versões. A tentativa iniciada anteriormente é então marcada como falha.

## Histórico não é backup

Cada versão registra o novo estado, com lote e instante. A migração também captura
os estados legados existentes. Isso permite acompanhar mudanças de negócio, mas não
substitui backup, controle de acesso nem cópia imutável dos arquivos recebidos.
O SHA-256 identifica o conteúdo do arquivo; ele não arquiva o arquivo.

Se uma ficha desaparecer do Excel, preservamos a ficha central. Ausência pode ser
exclusão, filtro, arquivo incompleto ou engano. Inativação precisa de regra explícita.
