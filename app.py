import streamlit as st
import json
import base64
from models import InvoiceData
from image_processor import process_image_upload, process_image_url, display_image_preview
from groq_client import GroqClient
from ui import setup_page, select_input_method, show_extraction_button, display_results, display_error

def main():
    setup_page()
    input_method = select_input_method()
    
    image_bytes = None
    image_url = None
    mime_type = "image/jpeg"
    
    if input_method == "Upload Image 📤":
        uploaded_file = st.file_uploader("Upload an invoice image", type=["png", "jpg", "jpeg"])
        image_bytes, mime_type = process_image_upload(uploaded_file)
    else:
        image_url = st.text_input("Enter image URL:")
        if image_url:
            try:
                image_bytes = process_image_url(image_url)
            except ValueError as e:
                display_error(str(e))
    
    if image_bytes:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader("Invoice Image")
            display_image_preview(image_bytes)
        
        with col2:
            st.subheader("Extracted Invoice Fields")
            if show_extraction_button():
                with st.spinner("Extracting data using LLaMA 4..."):
                    try:
                        groq_client = GroqClient(api_key=st.secrets["GROQ_API_KEY"])
                        
                        prompt = f"""
                        You are an intelligent OCR extraction agent capable of understanding and processing documents in multiple languages.
                        Given an image of an invoice, extract all relevant information in structured JSON format.
                        The JSON object must use the schema: {json.dumps(InvoiceData.model_json_schema(), indent=2)}
                        If any field cannot be found in the invoice, return it as null. Return the final result strictly in JSON format.
                        """
                        
                        if input_method == "Upload Image 📤":
                            base64_image = base64.b64encode(image_bytes).decode("utf-8")
                            image_content = {
                                "type": "image_url",
                                "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}
                            }
                        else:
                            image_content = {
                                "type": "image_url",
                                "image_url": {"url": image_url}
                            }
                        
                        extracted_data = groq_client.extract_invoice_data(prompt, image_content)
                        invoice = InvoiceData(**extracted_data)
                        display_results(invoice)
                    
                    except Exception as e:
                        display_error(f"Failed to parse invoice: {str(e)}")

if __name__ == "__main__":
    main()
