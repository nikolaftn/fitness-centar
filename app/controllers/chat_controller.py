from app.views.chat_view import ChatView


class ChatController:
    def __init__(
        self,
        parent,
        current_user_id,
        other_user_id,
        other_user_name,
        message_service,
    ):
        self.current_user_id = current_user_id
        self.other_user_id = other_user_id
        self.message_service = message_service
        self.view = ChatView(
            parent,
            self,
            current_user_id,
            other_user_name,
        )
        self.refresh()

    def refresh(self):
        try:
            messages = self.message_service.get_messages(
                self.current_user_id,
                self.other_user_id,
            )
        except ValueError as error:
            self.view.show_error(str(error))
            return
        self.view.clear_error()
        self.view.show_messages(messages)

    def send_message(self, _event=None):
        try:
            self.message_service.send_message(
                self.current_user_id,
                self.other_user_id,
                self.view.get_message(),
            )
        except ValueError as error:
            self.view.show_error(str(error))
            return
        self.view.clear_message()
        self.refresh()

    def focus(self):
        self.refresh()
        self.view.focus()

    def is_open(self):
        return self.view.is_open()

    def close(self):
        self.view.close()
