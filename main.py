from logic_chatbot import handle_message


def main():
    # Welcome message
    print("Logic Chatbot")
    print("Type 'exit' to quit")

    # Interactive loop
    while True:
        # prompt
        user_input = input("> ")

        # dispatch
        response = handle_message(user_input)

        # exit if handle_message returns None
        if response is None:
            print("Goodbye!")
            break

        # otherwise, show the chatbot’s reply
        print(response)


if __name__ == "__main__":
    main()
