from database.database import init_db, engine
from sqlmodel import Session
from models.user import Users
from models.request import PredictItem
from services.crud import user, transaction, service


if __name__ == '__main__':
    test_user_5 = Users(email='test5@mail.ru', username='Adam5',
                        password='test')

    init_db()
    print('Init db has been successful')

# Let's check all created functionality here below
    with Session(engine) as session:
        # User functionality
        user.create_user(test_user_5, session)
        user.add_balance(2, 40, session)
        user.deduct_balance(2, 5, session)
        balance_user_2 = user.check_balance(2, session)
        print(f'user_id_2 balance:{balance_user_2}')

        user_check_auth = user.authenticate('test5@mail.ru', 'test', session)
        print(f'user authenticate with id:{user_check_auth.user_id}')

        user_by_id_check = user.get_user_by_id(1, session)
        print(f'user with id=1 email:{user_by_id_check.email}')

        user_by_email_check = user.get_user_by_email('test1@example.com',
                                                     session)
        print(f'user email: test1@example.com \
              user id:{user_by_email_check.user_id}')

        admin_ = user.get_admin(session)
        print(f'admin id:{admin_.user_id}')

        balance_user_5 = user.check_balance(5, session)
        print(f'user_id_5 balance before adding by admin:{balance_user_5}')
        check_add_balance_by_admin = user.add_balance_to_user(admin_, 5,
                                                              100, session)
        balance_user_5 = user.check_balance(5, session)
        print(f'user_id_5 balance after adding by admin:{balance_user_5}')

        users = user.get_all_users(admin_, session)
        for user_ in users:
            print(f'id: {user_.user_id} - {user_.email} \
                 - {user_.is_admin} - {user_.balance}')

        # Transaction functionality
        transactions = transaction.view_all_transactions(admin_, session)
        for transaction_ in transactions:
            print(f'id:{transaction_.transaction_id} \
                  type:{transaction_.transaction_type} \
                  amount:{transaction_.amount} \
                  date:{transaction_.timestamp} \
                  user:{transaction_.user_id}')

        trans_check_by_user = transaction.get_transactions_by_user(2, session)
        for transaction_ in trans_check_by_user:
            print(f'id:{transaction_.transaction_id} \
                  type:{transaction_.transaction_type} \
                  amount:{transaction_.amount} \
                  date:{transaction_.timestamp} \
                  user:{transaction_.user_id}')

        # Service functionality
        models = service.get_all_models(session)
        for model_ in models:
            print(f'model_id:{model_.model_id} - location:{model_.location}')

        check_model_by_id = service.get_model_by_id(1, session)
        print(f'model id=1, location:{check_model_by_id.location}')

        check_model_load = service.load_model(check_model_by_id.location)
        print('model successfully loaded')

        test_data = PredictItem(
                fixed_acidity=0.5,
                volatile_acidity=0.3,
                citric_acid=0.1,
                residual_sugar=0.05,
                chlorides=1.2,
                free_sulfur_dioxide=0.2,
                total_sulfur_dioxide=0.9,
                density=3.2,
                pH=5.5,
                sulphates=0.4,
                alcohol=12,
        )
        check_prediction = service.make_prediction(check_model_load,
                                                   test_data)
        print(f'{check_prediction}')

        check_save_pred = service.save_prediction(1,
                                                  check_model_by_id.model_id,
                                                  test_data, check_prediction,
                                                  check_model_by_id.cost,
                                                  session)
        print('Prediction succsessfully saved')

        check_get_user_pred = service.get_predictions_by_user(1, session)
        for prediction_ in check_get_user_pred:
            print(f'prediction_id:{prediction_.prediction_id} \
                  user_id:{prediction_.user_id} \
                    model_id:{prediction_.model_id} \
                        input_data:{prediction_.input_data} \
                            prediction_result:{prediction_.prediction_result} \
                                cost:{prediction_.cost} \
                                    timestamp:{prediction_.timestamp}')

        check_process_request = service.process_request(check_model_by_id,
                                                        5, test_data, session)
        print('Process request succsessfully performed')

        check_all_preds = service.get_all_predictions(admin_, session)
        for prediction_ in check_all_preds:
            print(f'prediction_id:{prediction_.prediction_id} \
                  user_id:{prediction_.user_id} \
                    model_id:{prediction_.model_id} \
                        input_data:{prediction_.input_data} \
                            prediction_result:{prediction_.prediction_result} \
                                cost:{prediction_.cost} \
                                    timestamp:{prediction_.timestamp}')
