from enum import Enum, auto

import numpy as np
import pandas as pd
import streamlit as st


class FileFormat(Enum):
    csv = auto()
    tab = auto()
    fix = auto()
    custom = auto()

    def get_jpname(self) -> str:
        match self.name:
            case 'csv':
                return 'カンマ区切り'
            case 'tab':
                return 'タブ区切り'
            case 'fix':
                return '固定長'
            case 'custom':
                return '任意文字区切り'

    def get_specifier(self, delimit=' ') -> str:
        match self.name:
            case 'csv':
                return 'CSVDelimited'
            case 'tab':
                return 'TabDelimited'
            case 'fix':
                return 'FixedLength'
            case 'custom':
                if delimit == '':
                    return 'Delimited( )'
                else:
                    return f"Delimited({delimit})"


class ColType(Enum):
    # --Microsoft Jet data types--
    bit = 'Bit'
    byte = 'Byte'
    short = 'Short'
    long = 'Long'
    currency = 'Currency'
    single = 'Single'
    double = 'Double'
    datetime = 'DateTime'
    text = 'Text'
    memo = 'Memo'
    # --ODBC data types--
    # char = 'Char'
    # float = 'Float'
    # integer = 'Integer'
    # longchar = 'LongChar'
    # date = 'Date'


OPTIONS = [
    'CharacterSet',
    'DateTimeFormat',
    'DecimalSymbol',
    'NumberDigits',
    'NumberLeadingZeros',
    'CurrencySymbol',
    'CurrencyPosFormat',
    'CurrencyDigits',
    'CurrencyNegFormat',
    'CurrencyThousandSymbol',
    'CurrencyDecimalSymbol'
]


def callback_apply_edited_rows(
        key_data_editor: str,
        key_target: str
    ) -> None:
    """
    Apply edited rows to target dataframe

    parameters
    --------
    key_data_editor : str
        specified key at st.data_editor
    key_target : str
        key in st.session_state
        st.session_state[key_target] must be dataframe
    """
    dict_edited_rows = st.session_state[key_data_editor]['edited_rows']
    for idx, dict_edited_row in dict_edited_rows.items():
            for col, val in dict_edited_row.items():
                st.session_state[key_target].loc[idx, col] = val


def form_schemaini(
        filename: str,
        fileformat_specifier: str,
        is_header: bool,
        is_scan_rows: bool,
        max_scan_rows: int,
        df_cols: pd.DataFrame,
        df_options: pd.DataFrame
    ) -> str:
    """
    Form schema.ini content
    """
    content = f"[{filename}]\n"
    content += f"Format={fileformat_specifier}\n"
    content += f"ColNameHeader={is_header}\n"

    # Options
    df_options_sel = df_options.loc[df_options['value'].str.len() >= 1]

    if len(df_options_sel) >= 1:
        options = df_options_sel.apply(
            lambda row: f"{row['name']}={row['value']}",
            axis=1
        )
        content += '\n'.join(options)
        content += '\n'

    # Column type
    if is_scan_rows:
        content += f"MaxScanRows={max_scan_rows}\n"
    else:
        if fileformat_specifier == 'FixedLength':
            df_cols_sel = df_cols.loc[
                (df_cols['name'].str.len() >= 1)
                & (df_cols['type'].str.len() >= 1)
                & (df_cols['width'] >= 1)
            ]
        else:
            df_cols_sel = df_cols.loc[
                (df_cols['name'].str.len() >= 1)
                & (df_cols['type'].str.len() >= 1)
            ]

        def get_col(row: pd.Series) -> str:
            col = f"Col{row['Coln']}={row['name']} {row['type']}"
            if row['width'] >= 1:
                col += f" width {int(row['width'])}"
            return col

        cols = df_cols_sel.apply(get_col, axis=1)
        content += '\n'.join(cols)
        content += '\n'

    return content


def add_row() -> None:
    """
    add row to df_cols
    """
    data_row = {
        'Coln': [st.session_state['df_cols']['Coln'].max() + 1],
        'name': [''],
        'type': [''],
        'width': [np.nan]
    }
    df_row = pd.DataFrame(data_row)
    df_cols = pd.concat([st.session_state['df_cols'], df_row])
    df_cols = df_cols.reset_index(drop=True)
    st.session_state['df_cols'] = df_cols


def main():
    st.set_page_config(
        page_title='Schemaini',
        page_icon='☕',
        layout='wide'
    )
    st.title('Schemaini')
    st.write('schema.ini ファイル作成補助アプリ')

    col_input, col_output = st.columns([0.65, 0.35], border=True)

    with col_input:
        st.write(':memo: テキストファイルの情報を入力してください')

        # File name
        st.write(':material/Check: ファイル名')
        col1, col2, col3 = st.columns(
            [0.75, 0.05, 0.2],
            vertical_alignment='bottom'
        )

        with col1:
            stem = st.text_input(
                label='_',
                value='name',
                label_visibility='collapsed'
            )

        with col2:
            st.write('.')

        with col3:
            ext = st.text_input(
                label='_',
                value='csv',
                label_visibility='collapsed'
            )
        filename = f"{stem}.{ext}"

        col1, col2 = st.columns(2)

        with col1:
            # File format
            st.write(':material/Check: フォーマット')
            fileformat = st.radio(
                label='_',
                options=list(FileFormat),
                format_func=lambda x: x.get_jpname(),
                label_visibility='collapsed'
            )
            if fileformat == fileformat.custom:
                delimit = st.text_input(
                    label='区切り文字',
                    value='',
                    max_chars=1
                )
                if delimit == '"':
                    st.error('二重引用符 (") は使用できません')
                    delimit = ' '
                fileformat_specifier = fileformat.get_specifier(delimit)
            else:
                fileformat_specifier = fileformat.get_specifier()

        with col2:
            # Header
            st.write(':material/Check: ヘッダ')
            is_header = st.radio(
                label='_',
                options=[True, False],
                format_func=lambda x: 'あり' if x else 'なし',
                label_visibility='collapsed'
            )

        # Column type
        col1, col2 = st.columns(2)

        with col1:
            st.write(':material/Check: カラムの設定')

        with col2:
            if is_header:
                is_scan_rows = st.toggle(
                    label='データから型を判定',
                    value=False
                )
            else:
                is_scan_rows = False

            max_scan_rows = 0
            if is_scan_rows:
                max_scan_rows = st.number_input(
                    label='読み取る行数',
                    min_value=0,
                    value=0,
                    step=1,
                    help='0 で全行を読み取り'
                )

        if not is_scan_rows:
            column_config_cols = {
                'Coln': st.column_config.NumberColumn(
                    label='番号',
                    disabled=True,
                    required=True,
                    format='Col%d',
                    min_value=1,
                    step=1
                ),
                'name': st.column_config.TextColumn(
                    label='名称'
                ),
                'type': st.column_config.SelectboxColumn(
                    label='型',
                    options=[type.value for type in list(ColType)]
                ),
                'width': st.column_config.NumberColumn(
                    label='長さ',
                    min_value=1,
                    step=1,
                    help='固定長ファイルでは必須'
                ),
            }

            if 'df_cols' not in st.session_state:
                # Set df_cols in session_state
                initial_rows = 10
                data_cols = {
                    'Coln': [i for i in range(1, initial_rows + 1)],
                    'name': ['' for _ in range(initial_rows)],
                    'type': ['' for _ in range(initial_rows)],
                    'width': [np.nan for _ in range(initial_rows)]
                }
                df_cols = pd.DataFrame(data_cols)
                df_cols.loc[0, ['name', 'type']] = ['sample', 'Long']
                st.session_state['df_cols'] = df_cols

            st.data_editor(
                data=st.session_state['df_cols'],
                hide_index=True,
                column_config=column_config_cols,
                num_rows='fixed',
                key='edited_cols',
                on_change=callback_apply_edited_rows,
                args=('edited_cols', 'df_cols')
            )

            col1, col2 = st.columns([0.15, 0.85])
            with col1:
                if st.button(label=':material/add: 1'):
                    add_row()
                    st.rerun()
            with col2:
                if st.button(label=':material/add: 10'):
                    for _ in range(10):
                        add_row()
                    st.rerun()

            # Options
            st.write(':material/Check: オプション')

            with st.expander('値を指定'):
                column_config_options = {
                    'name': st.column_config.TextColumn(
                        label='項目',
                        disabled=True
                    ),
                    'value': st.column_config.TextColumn(
                        label='値'
                    ),
                }

                if 'df_options' not in st.session_state:
                    # Set df_options in session_state
                    data_options = {
                        'name': OPTIONS,
                        'value': ['' for _ in range(len(OPTIONS))]
                    }
                    df_options = pd.DataFrame(data_options)
                    st.session_state['df_options'] = df_options

                st.data_editor(
                    data=st.session_state['df_options'],
                    hide_index=True,
                    column_config=column_config_options,
                    num_rows='fixed',
                    key='edited_options',
                    on_change=callback_apply_edited_rows,
                    args=('edited_options', 'df_options')
                )

    with col_output:
        st.write(':sparkles: スキーマ情報 ( schema.ini )')
        content = form_schemaini(
            filename=filename,
            fileformat_specifier=fileformat_specifier,
            is_header=is_header,
            is_scan_rows=is_scan_rows,
            max_scan_rows=max_scan_rows,
            df_cols=st.session_state['df_cols'],
            df_options=st.session_state['df_options']
        )
        st.code(
            body=content,
            language=None
        )
        st.download_button(
            label='Download',
            data=content,
            file_name='schema.ini',
            on_click='ignore'
        )

    st.markdown("""
    * ブラウザ更新でリセットできます
    * schema.ini ファイルの詳細については [Microsoft Web サイト](https://learn.microsoft.com/ja-jp/sql/odbc/microsoft/schema-ini-file-text-file-driver?view=sql-server-ver17#understanding-schemaini-files) をご確認ください
    * schema.ini ファイルの扱いは、使用するアプリケーションの仕様に従います
    """)

if __name__ == '__main__':
    main()
