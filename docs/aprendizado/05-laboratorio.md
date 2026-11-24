# 5. Laboratório: aprenda provocando o sistema 🧪

Use cópias das planilhas e um banco descartável. Nunca use o banco principal do projeto
em `TEST_DATABASE_URL`: os testes de integração truncam as tabelas de trabalho.

## Missão 1 — Descobrir a linha

Crie uma planilha com título na linha 1, cabeçalho na 2, um projeto na 3, vazio na 4
e outro na 5. Rode a leitura. Por que o número físico precisa sobreviver à remoção
numa linha vazia? Veja `test_physical_line_blank_rows_and_na_preserved`.

## Missão 2 — Viajar no tempo

Carregue uma CI. Reexecute igual. Altere o setor e carregue novamente.
Você deve ter um projeto atual, três tentativas e duas versões.
O histórico mostra estados de negócio, a auditoria mostra execuções.

## Missão 3 — Derrubar o castelo pela metade

O teste `test_database_failure_rolls_back_data_and_history` cria uma restrição que
falha no segundo registro. Verifique que nem a primeira linha nem sua versão ficam
persistidas. Esse é o valor de uma transação, não apenas um `try/except`.

## Missão 4 — Duas pessoas na porta

O teste de concorrência tenta duas cargas iguais simultaneamente. O índice único
protege a chave; o bloqueio por ano organiza a comparação para evitar versões repetidas.

## Missão 5 — Planejar a dimensão

Desenhe uma dimensão Setor e uma fato Projeto. Pergunte: o setor de um projeto que
mudou deve aparecer como era na época ou como é hoje? Essa pergunta distingue estado
atual, histórico de versões e dimensão lentamente mutável. Não são a mesma coisa.

## Executar

```bash
python -m unittest discover -s tests -v
```

Sem `TEST_DATABASE_URL`, os testes com banco ficam explicitamente ignorados.
Com a variável, a suíte aplica as migrações em um banco descartável e verifica
inserção, atualização, histórico, vários anos, concorrência e rollback.
