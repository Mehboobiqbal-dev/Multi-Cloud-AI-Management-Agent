try:
    import speech_recognition as sr
    print("speech_recognition imported successfully!")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")