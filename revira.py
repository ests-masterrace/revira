from EduTalkAssistant import EduTalkAssistant
import sys

def main():
    if sys.version_info < (3, 8):
        print('Warning: EduTalk requires Python 3.8 or higher.')
    assistant = EduTalkAssistant()
    try:
        assistant.run()
    except KeyboardInterrupt:
        print("\nExiting EduTalk...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        assistant.shutdown()

if __name__ == "__main__":
    main()
