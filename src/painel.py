"""Execute com: streamlit run src/painel.py"""
import pandas as pd
import streamlit as st
from campus_etl.config import database_url
from campus_etl.queries import query, projects, project_count, filter_options, safe_csv
from campus_etl.presentation import LABELS, DEFAULT_COLUMNS, CATEGORICAL, visible_frame

st.set_page_config(page_title='Central de projetos', page_icon='📚', layout='wide')
st.title('Central de projetos')
st.caption('Encontre projetos de todos os anos e consulte suas informações.')
area = st.sidebar.radio('Área', ['Consultar projetos', 'Auditoria'], key='area')
st.sidebar.button('Atualizar consultas')
try:
    dsn = database_url(readonly=True)
    summary = query(dsn, 'SELECT * FROM mart.resumo_anual ORDER BY ano_origem DESC')
    if area == 'Auditoria':
        st.subheader('Histórico e acompanhamento de cargas')
        st.caption('Informações técnicas para acompanhamento da ingestão.')
        if not summary.empty:
            year = st.selectbox('Ano do projeto', summary.ano_origem.tolist())
            ci = st.text_input('Identificador (CI)', max_chars=200, key='project_ci')
            if ci:
                versions = query(dsn, '''SELECT versao_id, registrada_em, dados
                    FROM audit.demandas_versoes WHERE ano_origem=%s AND quant_ci=%s
                    ORDER BY versao_id DESC''', (int(year), ci.strip()))
                if versions.empty:
                    st.info('Nenhuma versão encontrada para essa chave.')
                for version in versions.to_dict('records'):
                    with st.expander(f"Versão {version['versao_id']} • {version['registrada_em']}"):
                        st.json(version['dados'])
        st.subheader('Últimas cargas')
        st.dataframe(query(dsn, '''SELECT arquivo_origem, ano_origem, iniciada_em, finalizada_em,
            status, linhas_lidas, linhas_carregadas, linhas_atualizadas, linhas_inalteradas,
            linhas_rejeitadas FROM audit.cargas ORDER BY iniciada_em DESC LIMIT 100'''),
            hide_index=True, width='stretch')
        st.stop()
    if summary.empty:
        st.info('Ainda não há projetos disponíveis para consulta.')
        st.stop()

    def clear_filters():
        for key in list(st.session_state):
            if key.startswith('filter_'):
                del st.session_state[key]
        st.session_state['search_query'] = ''
        st.session_state['years'] = summary.ano_origem.tolist()

    st.sidebar.subheader('Filtros')
    st.sidebar.button('Limpar filtros', on_click=clear_filters)
    if 'years' not in st.session_state:
        st.session_state['years'] = summary.ano_origem.tolist()
    years = st.sidebar.multiselect('Anos', summary.ano_origem.tolist(), key='years')
    search = st.sidebar.text_input('Busca geral', placeholder='Projeto, demandante, setor ou CI',
                                   max_chars=200, key='search_query')
    fields = st.sidebar.multiselect('Filtrar por colunas',
        [c for c in LABELS if c != 'ano_origem'], format_func=LABELS.get,
        default=['setor', 'unidade_regional', 'processo_finalizado'], key='filter_fields')
    filters = {}
    for column in fields:
        if column in CATEGORICAL:
            options = filter_options(dsn, years, column) if years else []
            key = f'filter_values_{column}'
            # Ao trocar os anos, remover somente seleções que deixaram de existir.
            if key in st.session_state:
                valid = [v for v in st.session_state[key] if v in options]
                if valid != st.session_state[key]:
                    st.session_state[key] = valid
            filters[column] = st.sidebar.multiselect(LABELS[column], options,
                format_func=lambda v: 'Não informado' if v is None else v,
                placeholder='Todos', key=key)
        else:
            filters[column] = st.sidebar.text_input(LABELS[column], placeholder='Contém…',
                                                     max_chars=200, key=f'filter_text_{column}')
    st.sidebar.caption('Filtros de colunas diferentes são combinados. Sem seleção significa todos. '
                       'Unidades regionais são filtradas conforme o texto da planilha.')
    with st.expander('Personalizar colunas da tabela'):
        columns = st.multiselect('Colunas visíveis', list(LABELS), default=DEFAULT_COLUMNS,
                                 format_func=LABELS.get, key='visible_columns')
    if not years:
        st.info('Selecione pelo menos um ano para consultar os projetos.')
        st.stop()
    total = project_count(dsn, years, search, filters)
    a, b = st.columns(2)
    a.metric('Projetos encontrados', total)
    b.metric('Anos selecionados', len(years))
    st.caption('O total considera a busca e todos os filtros selecionados.')
    if not total:
        st.info('Nenhum projeto encontrado. Ajuste os filtros ou use “Limpar filtros”.')
        st.stop()
    frame = projects(dsn, years, search, filters=filters)
    if total > len(frame):
        st.warning(f'Exibindo {len(frame)} de {total} projetos. Refine os filtros para visualizar e exportar o restante.')
    else:
        st.caption(f'{len(frame)} projetos disponíveis.')
    if columns:
        displayed = visible_frame(frame, columns).fillna('Não informado')
        st.dataframe(displayed, hide_index=True, width='stretch')
        st.download_button('Baixar tabela em CSV', safe_csv(displayed), 'projetos.csv', 'text/csv')
    else:
        st.info('Escolha pelo menos uma coluna para exibir a tabela e exportar.')
    with st.expander('Ver detalhes de um projeto'):
        detail_rows = {(int(r['ano_origem']), r['quant_ci']): r for r in frame.to_dict('records')}
        selected = st.selectbox('Projeto', list(detail_rows), index=None,
            placeholder='Selecione um projeto dos resultados', key='detail_project',
            format_func=lambda key: f"{key[0]} • {key[1]} • "
                                    f"{detail_rows[key]['evento_iniciativa'] or 'Projeto sem título'}")
        if selected is not None:
            details = visible_frame(pd.DataFrame([detail_rows[selected]]), list(LABELS)).iloc[0].fillna('Não informado')
            st.dataframe(pd.DataFrame({'Informação': details.index, 'Valor': details.astype(str).values}),
                         hide_index=True, width='stretch')
except Exception:
    st.error('Não foi possível consultar os projetos. Tente atualizar as consultas; se persistir, contate o responsável pela central.')
