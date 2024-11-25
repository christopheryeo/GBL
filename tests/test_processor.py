from processors import ProcessorFactory
import os

def test_kardex_processor():
    # Get the Kardex file from uploads directory
    uploads_dir = os.path.join(os.path.dirname(__file__), '..', 'uploads')
    kardex_file = None
    for file in os.listdir(uploads_dir):
        if file.endswith('.xlsx'):
            kardex_file = os.path.join(uploads_dir, file)
            break
    
    if not kardex_file:
        print("No Excel file found in uploads directory")
        return
        
    try:
        # Detect format
        format_type = ProcessorFactory.detect_format(kardex_file)
        print(f"Detected format: {format_type}")
        
        # Create processor
        processor = ProcessorFactory.create(format_type)
        
        # Process file
        df = processor.process(kardex_file)
        
        print("\nProcessed Data Sample:")
        print(df.head())
        print("\nColumns:", df.columns.tolist())
        print(f"\nTotal rows: {len(df)}")
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    test_kardex_processor()
