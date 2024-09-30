import streamlit as st
import pandas as pd
import requests

def main():
    uploaded_file = st.file_uploader("Import an XLSX file", type="xlsx")
       
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file, header=0)
            
            if len(df.columns) != 1:
                st.error("The uploaded file should contain only one column.")
            else:
                df.columns = ['Site']
                sites_list = df['Site'].tolist()

                with st.spinner('Processing URLs...'):
                    response = requests.post('http://194.164.72.188:4000/process_urls', json=sites_list)
                    
                    if response.status_code == 200:
                        out = pd.DataFrame(response.json())
                        st.dataframe(out)
                        
                        if not out.empty:
                            out.to_excel('GmapsDatas.xlsx', index=False)
                    else:
                        st.error(f"Error: {response.json().get('error')}")
        except Exception as e:
            st.error(f"An error occurred while processing the file: {str(e)}")
    user_input = st.text_input("Enter a search query for Google Maps:").lower().replace(' ', '+')
    
    if user_input:
        req = f"https://www.google.com/maps/search/{user_input}/"
        st.write(f"Searching: {req}")
        
        with st.spinner("Scraping data from Google Maps..."):
            response = requests.post('http://194.164.72.188:4000/scrape', json={'url': req})
            if response.status_code == 200:
                data = response.json()
                df = pd.DataFrame(data)
                st.dataframe(df)
                    
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download data as CSV",
                    data=csv,
                    file_name="google_maps_data.csv",
                    mime="text/csv",
                )
        

if __name__ == "__main__":
    main()
