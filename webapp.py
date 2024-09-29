import streamlit as st
import pandas as pd
import io
import ssl
from bs4 import BeautifulSoup
import asyncio
import aiohttp
import platform
import os
import stat
import psutil
import time
from seleniumbase import Driver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin

def set_seleniumbase_permissions():
    seleniumbase_dir = os.path.join(os.path.expanduser('~'), '.seleniumbase')
    if os.path.exists(seleniumbase_dir):
        for root, dirs, files in os.walk(seleniumbase_dir):
            for dir in dirs:
                os.chmod(os.path.join(root, dir), stat.S_IRWXU)
            for file in files:
                os.chmod(os.path.join(root, file), stat.S_IRWXU)
        st.success("SeleniumBase permissions set successfully.")
    else:
        st.warning("SeleniumBase directory not found. It will be created on first run.")

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

async def get_host(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [check_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
   
    return results

async def check_url(session, url):
    try:
        async with session.get(url, timeout=30, ssl=ssl_context) as response:
            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Check for specific hosts in the page content
            if 'thunderbolt' in str(soup) or 'DexVille' in str(soup) or 'Dexville' in str(soup):
                return 'Dexville'
            elif "You don't have permission to access this ressource" in str(soup) or 'Proximedia' in str(soup) or 'icon-logo-online' in str(soup) or 'icon-logo-afe' in str(soup) or 'BATIBOUW' in str(soup) or 'bizbook' in str(soup) or 'icon-logo-click-plus' in str(soup):
                return 'Proximédia'
            elif 'toponweb' in str(soup):
                return 'Toponweb'
            elif 'webforce' in str(soup) or 'Webforce' in str(soup):
                return 'Webforce'
            elif 'WEBCREAT' in str(soup):
                return 'Webcreat'
            elif 'http://www.savoirfaire.digital' in str(soup):
                return 'SFD'
            elif 'DIREXION Web Agency' in str(soup):
                return 'Direxion Web Agency'
            else:
                return 'Nothing Found'
    except: return None
    
def close_all_edge_instances():
    for process in psutil.process_iter(attrs=['pid', 'name']):
        try:
            if process.info['name'] == 'msedge.exe' or process.info['name'] == 'msedgedriver.exe':
                process.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def scrappe_gmaps(url):
    df = pd.DataFrame(columns=['Nom', 'Link', 'Adresse', 'Site', 'Telephone'])
    driver = Driver(headless=True, uc=True)
    s = time.time()
    driver.get(url)
    time.sleep(1)

    action = ActionChains(driver)
    a = driver.find_elements(By.CLASS_NAME, "hfpxzc")
    le = 0
    elements = []

    while len(a) < 1000:
        try:
            time.sleep(0.25)
            var = len(a)
            scroll_origin = ScrollOrigin.from_element(a[len(a)-1])
            action.scroll_from_origin(scroll_origin, 0, 1000).perform()
            time.sleep(2)
            a = driver.find_elements(By.CLASS_NAME, "hfpxzc")
            for _ in a:
                if _ not in elements:
                    elements.append(_)
        except: pass

        if len(a) == var:
            le+=1
            time.sleep(0.5)
            if le > 3:
                break
        else:
            le = 0

    for el in elements:
        driver.execute_script("arguments[0].scrollIntoView();", el)
        df.loc[len(df)] = [el.get_attribute('aria-label').replace('·Lien consulté', ''), el.get_attribute('href'), '', '', '']
        
    for index, row in df.iterrows():
        try:
            driver.get(row['Link'])
            tel, site, adresse = '', '', ''
            for t in WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'CsEnBe'))):
                aria = t.get_attribute('aria-label')
                if aria and 'Site Web' in aria:
                    site = aria.split(': ')[1].strip()
                elif aria and 'Numéro de téléphone' in aria:
                    tel = aria.split(': ')[1].strip()
                elif aria and 'Adresse' in aria:
                    adresse = aria.split(': ')[1].strip()
            df.at[index, 'Adresse'] = adresse
            df.at[index, 'Site'] = site
            df.at[index, 'Telephone'] = tel
        except: pass

    st.write(f"Scraping completed in {round(time.time() - s, 2)} seconds.")
    print(time.time() - s)
    driver.quit()
    close_all_edge_instances()
    return df


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
                            
                df = pd.DataFrame(columns=['Site'])
                df['Site'] = urls
                                       
                if platform.system() == 'Windows':
                    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                    
                with st.spinner('Processing URLs...'):
                    out = asyncio.run(mains(df))
                    
                st.dataframe(out)
                   
                if not out.empty:
                    out.to_excel('GmapsDatas.xlsx', index=False)
                   
        except: pass

    user_input = st.text_input("Enter a search query for Google Maps:").lower().replace(' ', '+')
    if user_input:
        req = f"https://www.google.com/maps/search/{user_input}/"
        st.write(f"Searching: {req}")
        
        with st.spinner("Scraping data from Google Maps..."):
            df = scrappe_gmaps(req)
            
        urls = df['Site'].unique().tolist()
        for i, url in enumerate(urls):
            if 'https://' not in url:
                urls[i] = f'https://{url}'
                   
        if platform.system() == 'Windows':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                    
        with st.spinner('Processing URLs...'):
            out = asyncio.run(mains(df))
                    
        st.success('Processing complete!')
        st.dataframe(out)
                   
        if not df.empty:
            out.to_excel('GmapsDatas.xlsx', index=False)
        else:
            st.error("No data scraped.")
        
async def mains(df):
    urls = df['Site'].unique().tolist()
    for i, url in enumerate(urls):
        if 'https://' not in url:
            urls[i] = f'https://{url}'
    
    hosts = await get_host(urls)
    url_host_mapping = dict(zip(urls, hosts))
    df['Host'] = df['Site'].apply(lambda site: url_host_mapping.get(f'https://{site}', 'Nothing Found'))
    
    return df
  

if __name__ == "__main__":
    set_seleniumbase_permissions()
    main()
