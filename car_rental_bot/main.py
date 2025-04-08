from bot_instance import bot
from database import initialize_db
import user_handlers
import admin_handlers

if __name__ == '__main__':
    #Ініціалізуємо базу даних 
    initialize_db()
    
    #Реєстрація обробників користувацьких та адміністративних команд
    user_handlers.register_user_handlers()
    admin_handlers.register_admin_handlers()
    
    bot.remove_webhook()

    print("Бот запущено...")
    bot.polling(none_stop=True)