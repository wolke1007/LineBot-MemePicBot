# -*- coding: utf-8 -*-
from models.bot.bot import Bot
from models.chat import Chat
from config import HELP_CONTENT
import unittest


class Event():
    '''
    mock data type
    '''
    reply_token = None

    class source():
        user_id = None
        group_id = None

    class message():
        text = None


class MemeBotTestCase(unittest.TestCase):

    def setUp(self):
        self.event = Event()

    def test_get_help(self):
        self.event.source.user_id = 'test_123'
        self.event.source.group_id = 'test_group'
        self.event.message.text = '--help'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), HELP_CONTENT)

    def test_set_pic_name_with_invalid_name(self):
        self.event.source.user_id = 'test_123'
        self.event.source.group_id = 'test_group'
        self.event.message.text = '#--pic_name_list#'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), '-- 開頭的名字為系統保留禁止使用')
        
    def test_set_pic_name_with_valid_name(self):
        self.event.source.user_id = 'test_123'
        self.event.source.group_id = 'test_group'
        self.event.message.text = '#set_pic_name_test#'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), '圖片名稱已設定: set_pic_name_test，請上傳圖片或圖片連結')

    def test_set_pic_name_with_same_valid_name_again_after_did_it_before(self):
        self.event.source.user_id = 'test_123'
        self.event.source.group_id = 'test_group'
        self.event.message.text = '#set_pic_name_test#'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), '圖片名稱已更新: set_pic_name_test，請上傳圖片或圖片連結')

    def test_set_pic_name_with_diff_valid_name_again_after_did_it_before(self):
        self.event.source.user_id = 'test_123'
        self.event.source.group_id = 'test_group'
        self.event.message.text = '#pic_name_update_test#'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), '圖片名稱已更新: pic_name_update_test，請上傳圖片或圖片連結')

    def test_set_pic_name_with_valid_name_again_after_did_it_before(self):
        self.event.source.user_id = 'test_123'
        self.event.source.group_id = 'test_group'
        self.event.message.text = '#pic_name_update_test#'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), '圖片名稱已更新: pic_name_update_test，請上傳圖片或圖片連結')

    def test_delete_pic_with_same_user_diff_group(self):
        self.event.source.user_id = 'test_123'
        self.event.source.group_id = 'test_group2'
        self.event.message.text = '--delete pic_name_update_test'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), '圖片未刪除\n(提醒: 不能刪除別人的圖片，也不能刪除其他聊天室的圖片)')

    def test_delete_pic_with_diff_user_same_group(self):
        self.event.source.group_id = 'test_group'
        self.event.source.user_id = 'test_1234'
        self.event.message.text = '--delete pic_name_update_test'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), '圖片未刪除\n(提醒: 不能刪除別人的圖片，也不能刪除其他聊天室的圖片)')

    def test_delete_pic_with_diff_user_diff_group(self):
        self.event.source.user_id = 'test_1234'
        self.event.source.group_id = 'test_group2'
        self.event.message.text = '--delete pic_name_update_test'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), '圖片未刪除\n(提醒: 不能刪除別人的圖片，也不能刪除其他聊天室的圖片)')

    def test_delete_pic_with_same_user_same_group(self):
        self.event.source.user_id = 'test_123'
        self.event.source.group_id = 'test_group'
        self.event.message.text = '--delete pic_name_update_test'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), 'pic_name_update_test 已刪除')

    def test_delete_pic_with_same_user_same_group(self):
        self.event.source.user_id = 'test_123'
        self.event.source.group_id = 'test_group'
        self.event.message.text = '--delete pic_name_update_test'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), 'pic_name_update_test 已刪除')

    def test_reply_pic_name_list(self):
        self.event.source.user_id = 'test_123'
        self.event.source.group_id = 'test_group'
        self.event.message.text = '--list'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func()[:20], 'https://i.imgur.com/')

    def test_send_pic_back(self):
        self.event.source.user_id = 'test_123'
        self.event.source.group_id = 'test_group'
        self.event.message.text = 'I will find you'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), 'https://i.imgur.com/ri8FJaY.jpg')

    def test_show_current_mode(self):
        self.event.source.user_id = 'test_123'
        self.event.source.group_id = 'test_group'
        self.event.message.text = '--mode'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(),
                         ("[當前模式為]\n"+
                          "chat_mode: 隨機回所有群組創的圖(此為預設)\n"
                          "retrieve_pic_mode: 此功能尚未實作\n"
                          "trigger_chat: 僅回覆字數大於等於 3 的圖片"))

    def test_chat_mode_change(self):
        self.event.source.user_id = 'test_123'
        self.event.source.group_id = 'test_group'
        self.event.message.text = '--mode chat_mode A'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), ("chat_mode 後需設定介於 0~2 的數字，"
                                           "如 --mode chat_mode 2"))
        self.event.message.text = '--mode chat_mode 3'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), ("chat_mode 後需設定介於 0~2 的數字，"
                                           "如 --mode chat_mode 2"))
        self.event.message.text = '--mode chat_mode 0'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), '更改聊天模式為: 不回圖')
        self.event.message.text = 'I will find you'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), None)
        self.event.message.text = '--mode chat_mode 2'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), '更改聊天模式為: 只回該群組上傳的圖')
        self.event.message.text = 'I will find you'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), None)
        self.event.message.text = '--mode chat_mode 1'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), '更改聊天模式為: 隨機回所有群組創的圖(此為預設)')
        self.event.message.text = 'I will find you'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), 'https://i.imgur.com/ri8FJaY.jpg')

    def test_trigger_chat_change(self):
        self.event.source.user_id = 'test_123'
        self.event.source.group_id = 'test_group'
        self.event.message.text = '--mode trigger_chat 1'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), ("trigger_chat 後需設定介於 2~15 的數字"
                                           "，如 --mode trigger_chat 15"))
        self.event.message.text = '--mode trigger_chat ABC'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), ("trigger_chat 後需設定介於 2~15 的數字"
                                           "，如 --mode trigger_chat 15"))
        self.event.message.text = '--mode trigger_chat 4'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), ("僅回覆字數大於等於 4 的圖片"))
        self.event.message.text = 'wtf'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), None)
        self.event.message.text = '--mode trigger_chat 3'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), ("僅回覆字數大於等於 3 的圖片"))
        self.event.message.text = 'wtf'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), 'https://i.imgur.com/mv07XhN.jpg')


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    suite = unittest.TestSuite()
    suite.addTest(MemeBotTestCase("test_get_help"))
    suite.addTest(MemeBotTestCase("test_set_pic_name_with_invalid_name"))
    suite.addTest(MemeBotTestCase("test_set_pic_name_with_valid_name"))
    suite.addTest(MemeBotTestCase("test_set_pic_name_with_same_valid_name_again_after_did_it_before"))
    suite.addTest(MemeBotTestCase("test_set_pic_name_with_diff_valid_name_again_after_did_it_before"))
    suite.addTest(MemeBotTestCase("test_set_pic_name_with_valid_name_again_after_did_it_before"))
    suite.addTest(MemeBotTestCase("test_delete_pic_with_same_user_diff_group"))
    suite.addTest(MemeBotTestCase("test_delete_pic_with_diff_user_same_group"))
    suite.addTest(MemeBotTestCase("test_delete_pic_with_diff_user_diff_group"))
    suite.addTest(MemeBotTestCase("test_delete_pic_with_same_user_same_group"))
    suite.addTest(MemeBotTestCase("test_reply_pic_name_list"))
    suite.addTest(MemeBotTestCase("test_send_pic_back"))
    suite.addTest(MemeBotTestCase("test_show_current_mode"))
    suite.addTest(MemeBotTestCase("test_chat_mode_change"))
    suite.addTest(MemeBotTestCase("test_trigger_chat_change"))
    runner.run(suite)
