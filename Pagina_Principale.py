# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import streamlit as st
from streamlit.logger import get_logger
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader


LOGGER = get_logger(__name__)

def run():
    st.set_page_config(
        page_title="Albero Genealogico",
        page_icon="👋",
    )    
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
        
        st.write(f'Welcome *{st.session_state["name"]}*')
        st.write("# Albero Genealogico! 👋")

        st.sidebar.success("Seleziona un menú qui sopra.")
        st.markdown(
                    """
        Questa applicazione verrá usata per controllare 
        quali cognomi sono giá stati cercati e per quali anni        
        **👈 Seleziona un menú dalla barra laterale** per accedere!
        
        """)
    elif st.session_state["authentication_status"] is False:
        st.error('Username/password is incorrect')
    elif st.session_state["authentication_status"] is None:
       st.warning('Please enter your username and password')

if __name__ == "__main__":
    run()
