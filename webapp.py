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
    search_button = st.button("Search")
    
    if user_input and search_button:
        # Construct the request URL
        req = f"https://www.google.com/maps/search/{user_input}/"
        st.write(f"Searching: {req}")
        
        # Error handling block
        try:
            with st.spinner("Scraping data from Google Maps..."):
                # Send a request to your backend
                headers = {'Connection': 'keep-alive'}
                response = requests.post('http://194.164.72.188:4000/scrape', json={'url': req}, headers=headers)
                
                # Check if the response is successful
                if response.status_code == 200:
                    data = response.json()

                    # If no data is returned, handle it gracefully
                    if not data:
                        st.warning("No data found for the given query.")
                    else:
                        # Convert the data to a DataFrame and display it
                        df = pd.DataFrame(data)
                        df = df[['Nom', 'Link', 'Adresse', 'Telephone', 'Site', 'Host']]
                        st.dataframe(df)

                        # Allow CSV download
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="Download data as CSV",
                            data=csv,
                            file_name="google_maps_data.csv",
                            mime="text/csv",
                        )
                else:
                    # Display error message for unsuccessful status codes
                    st.error(f"Error: Received status code {response.status_code} from the server.")
        
        except requests.exceptions.RequestException as e:
            # Catch any request-related errors and display them
            st.error(f"Request failed: {e}")
        except Exception as e:
            # Catch any other unforeseen errors
            st.error(f"An error occurred: {e}")
        

if __name__ == "__main__":
    main()
