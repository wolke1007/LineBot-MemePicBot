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

    def test_mode_change(self):
        self.event.source.user_id = 'test_123'
        self.event.source.group_id = 'test_group'
        self.event.message.text = '--mode chat_mode 0'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), '更改 chat_mode 為 0')
        self.event.message.text = 'I will find you'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), None)
        self.event.message.text = '--mode chat_mode 2'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), '更改 chat_mode 為 2')
        self.event.message.text = 'I will find you'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), None)
        self.event.message.text = '--mode chat_mode 1'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), '更改 chat_mode 為 1')
        self.event.message.text = 'I will find you'
        chat = Chat(self.event, is_image_event=False)
        bot = Bot(chat, debug=True)
        self.assertEqual(bot.test_func(), 'https://i.imgur.com/ri8FJaY.jpg')


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
    suite.addTest(MemeBotTestCase("test_mode_change"))
    runner.run(suite)
