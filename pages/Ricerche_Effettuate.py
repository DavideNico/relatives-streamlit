import streamlit as st
from streamlit.logger import get_logger
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import duckdb
import pandas as pd
from datetime import datetime
import re
import base64





con=duckdb.connect('alberogenealogico.db',read_only=True)
data = con.sql('''SELECT * FROM LINKS_TO_REGISTRY''').df()
con.close()
def make_clickable(link):
                            # target _blank to open new window
                            # extract clickable text to display for your link
                            text = link.split('=')[1]
                            return f'<a target="_blank" href="{link}">{text}</a>'


def download_db_file():
    """
    Function to prepare the .db file for download.
    """
    # Assuming your .db file name is 'example.db'
    db_file_path = 'searches.db'
    with open(db_file_path, 'rb') as f:
        db_file_data = f.read()
    b64_data = base64.b64encode(db_file_data).decode('utf-8')
    href = f'<a href="data:application/octet-stream;base64,{b64_data}" download="searches.db">Download .db file</a>'
    st.markdown(href, unsafe_allow_html=True)

# Add a button to trigger the download

def run_query(query,read_only=False):
    con=duckdb.connect('searches.db',read_only=read_only)
    data = con.sql(query).df()
    con.close()
    return (data)
st.set_page_config(layout="wide")
with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

        authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized']
        )
        authenticator.login()

if st.session_state["authentication_status"]:
        authenticator.logout()
        
        st.write(f'Benvenuto *{st.session_state["name"]}*')
        
        Type=sorted(list(data.Tipologia.unique()))
        Year=sorted(list(data.Anno.unique()))
        Commune=sorted(list(data.Comune.unique()))
        with st.sidebar:                            
                Tipologia = st.selectbox('Tipologia',Type)
                Anno = st.selectbox('Anno',Year)
                Comune = st.selectbox('Comune',Commune)        
        
        datafr_cont=st.container(border=True)
        datafr_cont.title("Interfaccia per inserimento ricerche")
        datafr_cont.subheader('''Qui puoi inserire i cognomi che ricerchiamo.''',divider='rainbow')
        datafr_cont.markdown('''
                             1. Seleziona i filtri a sinistra
                             2. Clicca il link al documento e cerca i Cognomi
                             3. Inserisci il Cognome che stai cercando e clicca invio
                                (La prima lettera deve essere maiuscola -> Nicolini)
                             4. Inserisci il numero di persone trovate
                                a. Se 0 clicca su "Salva la ricerca"
                                b. Se piú di 0 inserisci i nomi e il link alla pagina e poi clicca "Salva la ricerca"                                
                             
                             ''')

        Archivio_df=data[(data['Anno']==Anno)&(data['Comune']==Comune)&(data['Tipologia']==Tipologia)]
        if len(Archivio_df)==0:
            datafr_cont.info('Nessun risultato, seleziona altri filtri.', icon="🤖")
        else:
            datafr_cont.dataframe(Archivio_df,                     
                     column_config={"Link": st.column_config.LinkColumn("Link al documento")
                                    ,"Anno": st.column_config.NumberColumn("Link al documento",format="%d")},) 
        
            input_cont=st.container(border=True)
            cognome=datafr_cont.text_input(label='Inserisci il Cognome')

            if cognome=='':
                datafr_cont.warning('Inserisci un cognome', icon="🚨")
            else:
                df_search=run_query(f'''SELECT * FROM SEARCHES 
                            where UPPER(COGNOME) = TRIM(UPPER('{cognome}'))
                            and Anno = {Anno}
                            and Tipologia = '{Tipologia}'
                            and Comune = '{Comune}'                         
                            ''')
                
                if len(df_search)>0:
                    datafr_cont.write('Nomi trovati nei seguenti registri:')
                    name_list=df_search['NOME_TROVATO'].str.split('|',expand=True)
                    link_list=df_search['LINK_ALLE_PAGINE'].str.split('|',expand=True)
                    existing_names=pd.concat([name_list.transpose(),link_list.transpose()],axis=1)
                    existing_names.columns=['Nome','Link alla pagina']
                    existing_names['Cognome']= cognome                    
                    existing_names['Utente']=df_search['UTENTE']
                    existing_names['Data Inserimento']=df_search['DATA_RICERCA']



                    datafr_cont.dataframe(existing_names,                     
                        column_config={"Link alla pagina": st.column_config.LinkColumn("Link alla pagina")},
                        use_container_width=False,
                                       )
                else:
                    datafr_cont.warning('Cognome non ricercato', icon="🔥")
                    number_of_person_found=datafr_cont.number_input('Quante persone hai trovato?',min_value=0)
                    if number_of_person_found>0:
                          d_name={}
                          d_link={}
                          for i in range(number_of_person_found):                            
                            k=f'Name {i+1}'                            
                            v=''
                            d_name[k]=v

                            k1=f'Link {i+1}'
                            d_link[k1]=v

                          col1,col2= input_cont.columns(2)                          
                          col1.header('Nome')
                          col2.header('Link alla pagina')

                          for i, (name_key, link_key) in enumerate(zip(d_name.keys(), d_link.keys())):
                            with col1:                                                                
                                d_name[name_key] = st.text_input(name_key, d_name[name_key])

                            with col2:
                                d_link[link_key] = st.text_input(link_key, d_link[link_key])
                          
                          if st.button(':face_with_monocle: Salva la ricerca', key=1):
                            link_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
                            link_list_checked=[bool(link_pattern.match(value)) for value in d_link.values()]
                            link_str=' | '.join(d_link.values())
                            nomi_str='|'.join(d_name.values())
                            if (link_str.replace('|','').replace(' ','')=='') or (nomi_str.replace('|','').replace(' ','')=='') :
                                st.error('Per favore inserisci tutti i valori prima di cliccare', icon='🚫')
                            elif any(value == False for value in link_list_checked):
                                st.error('Uno o piú link che hai inserito non sono corretti.', icon='🚫')
                            else:
                                    output=Archivio_df                                    
                                    output['COGNOME']=cognome
                                    output['DATA_RICERCA']=datetime.now().strftime("%Y-%m-%d")
                                    output['UTENTE']=st.session_state["name"]
                                    output['PERSONE_TROVATE']=number_of_person_found
                                    output['LINK_ALLE_PAGINE']=link_str
                                    output['NOME_TROVATO']=nomi_str
                                    #st.dataframe(output)
                                    try:
                                        con=duckdb.connect('searches.db')
                                        col=list(con.sql('''SELECT * FROM SEARCHES''' ).df().columns)
                                        col=','.join(col)
                                        con.sql(f'''INSERT INTO SEARCHES ({col}) select {col} from output ''' )
                                        con.close()
                                        st.balloons()
                                    except Exception as e:
                                        st.write(f'something went wrong: {e}')
                                        con.close()
                    elif number_of_person_found==0:
                        if st.button(':face_with_monocle: Salva la ricerca',key=2):
                            link_str=''
                            nomi_str=''
                            output=Archivio_df                                    
                            output['COGNOME']=cognome
                            output['DATA_RICERCA']=datetime.now().strftime("%Y-%m-%d")
                            output['UTENTE']=st.session_state["name"]
                            output['PERSONE_TROVATE']=number_of_person_found
                            output['LINK_ALLE_PAGINE']=link_str
                            output['NOME_TROVATO']=nomi_str
                            #st.dataframe(output)
                            try:
                                con=duckdb.connect('searches.db')
                                col=list(con.sql('''SELECT * FROM SEARCHES''' ).df().columns)
                                col=','.join(col)
                                con.sql(f'''INSERT INTO SEARCHES ({col}) select {col} from output ''' )
                                con.close()
                                st.balloons()
                            except Exception as e:
                                st.write(f'something went wrong: {e}')
                                con.close()
        st.divider()
        general_cognome_cont=st.container(border=True)
        general_cognome_cont.title('Ritrovamenti per Cognome')
        general_cognome_cont.subheader('Qui puoi inserire un cognome e vedere i documenti in cui é stato trovato', divider='rainbow')
        col_1,col_2= general_cognome_cont.columns(2)
        with col_1:
            cogn_ricerca=st.text_input(label='Inserisci il Cognome',key=3)
        with col_2:
            ricerca_gen_button=st.button('Clicca per cercare')
        if ricerca_gen_button:
            try:
                df_out=run_query(f'''SELECT * FROM SEARCHES 
                                where UPPER(COGNOME) = TRIM(UPPER('{cogn_ricerca}'))
                                order by Comune,Tipologia, Anno                        
                                ''')  
                general_cognome_cont.dataframe(df_out,                     
                     column_config={"Link": st.column_config.LinkColumn("Link al documento")
                                    ,"Anno": st.column_config.NumberColumn("Link al documento",format="%d") },)          
            except Exception as e:
                st.write(f'something went wrong: {e}')
                con.close()       
        st.divider()
        if st.button("Download .db file"):
            download_db_file()
elif st.session_state["authentication_status"] is False:
        st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
       st.warning('Please enter your username and password')