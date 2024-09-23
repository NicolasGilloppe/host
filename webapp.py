import streamlit as st
import pandas as pd
import io
import ssl
from bs4 import BeautifulSoup
import asyncio
import aiohttp
import platform

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

async def get_host(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [check_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
   
    res = pd.DataFrame(results, columns=['Urls', 'Host'])
    return res

async def check_url(session, url):
    try:
        async with session.get(url, timeout=30, ssl=ssl_context) as response:
            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
               
            if 'thunderbolt' in str(soup) or 'DexVille' in str(soup) or 'Dexville' in str(soup):
                return url, 'Dexville'
            elif "You don't have permission to access this ressource" in str(soup) or 'Proximedia' in str(soup) or 'icon-logo-online' in str(soup) or 'icon-logo-afe' in str(soup) or 'BATIBOUW' in str(soup) or 'bizbook' in str(soup) or 'icon-logo-click-plus' in str(soup):
                return url, 'Proximédia'
            elif 'toponweb' in str(soup):
                return url, 'Toponweb'
            elif 'webforce' in str(soup) or 'Webforce' in str(soup):
                return url, 'Webforce'
            elif 'WEBCREAT' in str(soup):
                return url, 'Webcreat'
            elif 'http://www.savoirfaire.digital' in str(soup):
                return url, 'SFD'
            elif 'DIREXION Web Agency' in str(soup):
                return url, 'Direxion Web Agency'
            else:
                return url, 'Nothing Found'
    except Exception as e:
        return url, None

def main():   
    uploaded_file = st.file_uploader("Import an XLSX file", type="xlsx")
   
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file, header=0)
           
            if len(df.columns) != 1:
                st.error("The uploaded file should contain only one column.")
            else:
                df.columns = ['Urls']
                urls = df['Urls'].unique().tolist()
                for i, url in enumerate(urls):
                    if 'https://' not in url:
                        urls[i] = f'https://{url}'
               
                if platform.system() == 'Windows':
                    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                
                with st.spinner('Processing URLs...'):
                    out = asyncio.run(mains(urls))
                
                st.success('Processing complete!')
                st.dataframe(out)
               
                if not out.empty:
                    excel_file = to_excel(out)
                    st.download_button(
                        label="Download results",
                        data=excel_file,
                        file_name="results.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
               
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

async def mains(urls):
    re = await get_host(urls)
    return re

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    processed_data = output.getvalue()
    return processed_data

if __name__ == "__main__":
    main()
