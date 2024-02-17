import streamlit as st
from streamlit.logger import get_logger
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import duckdb
import pandas as pd
from datetime import datetime






con=duckdb.connect('alberogenealogico.db',read_only=True)
data = con.sql('''SELECT * FROM LINKS_TO_REGISTRY''').df()
con.close()
def make_clickable(link):
                            # target _blank to open new window
                            # extract clickable text to display for your link
                            text = link.split('=')[1]
                            return f'<a target="_blank" href="{link}">{text}</a>'

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
        st.write("# Le nostre ricerche ")
        st.markdown(
                    """Qui puoi trovare i cognomi che abbiamo giá ricercato. 
                    Seleziona i filtri a sinistra per definire la ricerca
        """)
        Type=sorted(list(data.Tipologia.unique()))
        Year=sorted(list(data.Anno.unique()))
        Commune=sorted(list(data.Comune.unique()))
        with st.sidebar:                            
                Tipologia = st.selectbox('Tipologia',Type)
                Anno = st.selectbox('Anno',Year)
                Comune = st.selectbox('Comune',Commune)        
        
        datafr_cont=st.container(border=True)

        Archivio_df=data[(data['Anno']==Anno)&(data['Comune']==Comune)&(data['Tipologia']==Tipologia)]
        if len(Archivio_df)==0:
            datafr_cont.info('Nessun risultato, seleziona altri filtri.', icon="🤖")
        else:
            datafr_cont.dataframe(Archivio_df,                     
                     column_config={"Link": st.column_config.LinkColumn("Link al documento")},use_container_width=False,) 
        
            cognome_cont=st.container(border=True)
            input_cont=st.container(border=True)
            cognome=cognome_cont.text_input(label='Inserisci il Cognome')

            if cognome=='':
                cognome_cont.warning('Inserisci un cognome', icon="🚨")
            else:
                df_search=run_query(f'''SELECT * FROM SEARCHES 
                            where UPPER(COGNOME) = TRIM(UPPER('{cognome}'))
                            and Anno = {Anno}
                            and Tipologia = '{Tipologia}'
                            and Comune = '{Comune}'                         
                            ''')
                
                if len(df_search)>0:
                    cognome_cont.write('Nomi trovati nei seguenti registri:')
                    name_list=df_search['NOME_TROVATO'].str.split('|',expand=True)
                    link_list=df_search['LINK_ALLE_PAGINE'].str.split('|',expand=True)
                    existing_names=pd.concat([name_list.transpose(),link_list.transpose()],axis=1)
                    existing_names.columns=['Nome','Link alla pagina']
                    existing_names['Cognome']= cognome                    
                    existing_names['Utente']=df_search['UTENTE']
                    existing_names['Data Inserimento']=df_search['DATA_RICERCA']



                    cognome_cont.dataframe(existing_names,                     
                        column_config={"Link alla pagina": st.column_config.LinkColumn("Link alla pagina")},
                        use_container_width=False,
                                       )
                else:
                    cognome_cont.warning('Cognome non ricercato', icon="🔥")
                    number_of_person_found=cognome_cont.number_input('Quante persone hai trovato?',min_value=0)
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

                          for k,v in d_name.items():
                            with col1:                                                                
                                    d_name[k]=st.text_input(k,v)

                          for k,v in d_link.items():
                            with col2:
                                    d_link[k]=st.text_input(k,v)
                          
                            if st.button(':face_with_monocle: Salva la ricerca'):
                                link_str=' | '.join(d_link.values())
                                nomi_str='|'.join(d_name.values())
                                if (link_str.replace('|','').replace(' ','')=='') or ((nomi_str.replace('|','').replace(' ','')=='')):
                                        st.error('Per favore inserisci tutti i valori prima di cliccare', icon='🚫')
                                else:
                                        output=Archivio_df                                    
                                        output['COGNOME']=cognome
                                        output['DATA_RICERCA']=datetime.now().strftime("%Y%m%d")
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
                          if st.button(':face_with_monocle: Salva la ricerca'):
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

                                
            


                

        

elif st.session_state["authentication_status"] is False:
        st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
       st.warning('Please enter your username and password')