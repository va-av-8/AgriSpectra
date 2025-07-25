# AgriSpectra 

## 1.  Бизнес-анализ (Business Understanding)   

- **Видение проекта:** Разработать сельскохозяйственную платформу на базе искусственного интеллекта, которая будет сочетать анализ изображений сельскохозяйственных культур, сделанных с помощью смартфона или дрона, и спутниковых данных, чтобы помочь диагностировать проблемы на ранней стадии и прогнозировать урожайность, предоставлять рекомендаций по уходу для каждой детектированной культуры, стадии роста, типа и степени повреждения.
- **Коммерческая цель**: Снижение потерь урожая и повышение эффективности агробизнеса за счёт мобильной диагностики и спутниковой аналитики.
- **Технологическая цель**: Интеграция компьютерного зрения (анализ фото) и спутниковых данных для получения прогнозов и выявления угроз на разных масштабах (от листа до поля).
- **Целевая аудитория**:
  - Малые и средние фермеры
  - Крупные агропредприятия и агрохолдинги
- **Решаемые проблемы**:
  - Потери урожая из-за болезней/вредителей
  - Отсутствие прогнозов урожайности
  - Отсутствие адаптации к климатическим рискам
      
- **Организационная структура проекта:** проект выполняется без участия заказчика, с поддержкой эксперов AI Talent Hub (чат в Пачке: https://app.pachca.com/chats/14334466)     
      
- **Анализ 10 глобальных решений** в сфере АПК (агропромышленного комплекса),  мобильной диагностики и спутникового мониторинга.



| Компания / Продукт         | Мобильная диагностика | Спутниковые данные | Определение стадии роста | Обнаружение повреждений | Прогноз урожайности | 
|----------------------------|-----------------------|--------------------|--------------------------|-------------------------|---------------------|
| Plantix                    | Да                    | Нет                | Нет                      | Да                      | Нет                 | 
| PlantVillage Nuru          | Да                    | Частично           | Ограничено               | Да                      | Частично            | 
| Agrio                      | Да                    | Да                 | Нет                      | Да                      | Нет                 | 
| Taranis                    | Нет (только дроны)    | Да                 | Нет                      | Да                      | Нет                 | 
| OneSoil                    | Нет                   | Да                 | Частично (по NDVI)       | Частично                | Нет                 | 
| EOS Crop Monitoring        | Нет                   | Да                 | Да                       | Частично (по NDVI)      | Да                  | 
| SatSure                    | Нет                   | Да                 | Частично                 | Частично                | Да                  | 
| Climate FieldView          | Нет                   | Да                 | Частично                 | Частично                | Частично            | 
| Farmers Edge               | Нет                   | Да                 | Нет                      | Частично                | Да                  | 
| Descartes Labs             | Нет                   | Да                 | Нет                      | Нет                     | Да                  | 

 **Вывод**: нет решений, которые **одновременно** покрывают:
 - анализ фото с мобильного устройства
 - анализ спутниковых данных
 - автоматическое определение стадии роста
 - обнаружение поврежданий
 - прогноз урожайности  
Наш продукт закрывает этот пробел.

    
### 1.1. Текущая ситуация (Assessing current solution)   
 - Для обучения моделей на стадии прототипа будет использован Kaggle / Google collab. Для стадий MVP - аренда облачных ресурсов. Для инференса - аренда облачных ресурсов на всех стадиях.   
 - На стадии прототипа обучение будет проводится на датасете Eyes on the Groud (https://source.coop/repositories/lacuna/eyes-on-the-ground/description).    
 - Будет привлечена помощь двух мелких фермерских хозяйств для оценки качества модели на финальных стадиях обучения и для оценки удобства сервиса.    

**Риски** и стратегии их смягчения

| Риск                                                        | Стратегия смягчения                                                                                 |
|-------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| Не уложиться в сроки                                        | Разбивка задач на спринты, приоритизация core-функций, итеративная разработка                       |
| Недостаток изображений высокого качества                    | Аугментация, добор из датасета KaraAgroAI/Drone-based-Agricultural-Dataset-for-Crop-Yield-Estimation|
| Слабая различимость повреждений по изображениям             | Упрощение задачи (здоров/нездоров), фокус на ключевые классы                                        |
| Нестабильная работа модели в полевых условиях               | Аугментация, обучение на «шумных» изображениях, проверка качества фото в приложении                 |
| Недостаток исторических данных для обучения модели прогноза | Использование региональной агростатистики, моделей роста, поиск дополнительных данных               |
| Пропуски в спутниковых данных из-за облачности              | Интеграция SAR-данных, интерполяция                                                                 |
| Отсутствие закономерностей в данных                         | Уточнение фичей (почвы, агротехника), кластеризация по регионам, переопределение задачи             |


### 1.2 Решаемые задачи с точки зрения аналитики (Data Mining goals)    

#### Метрики оценки

 - **Модели на основе изображений**

| Назначение                             | Метрика                              | Комментарий                                                                                    |
|----------------------------------------|--------------------------------------|------------------------------------------------------------------------------------------------|
| Классификация культуры                 | Accuracy, F1-score, Confusion Matrix | Доля верно определённых классов, баланс точности и полноты, отображение точности между классами|
| Распознавание стадии роста             | Accuracy, F1-score, Confusion Matrix | Доля верно определённых классов, баланс точности и полноты, отображение точности между классами|
| Диагностика наличия и типа повреждения | Accuracy, F1-score, Confusion Matrix | Доля верно определённых классов, баланс точности и полноты, отображение точности между классами|
| Оценка площади повреждений             | mIoU                                 | Качество сегментации по площади поражения                                                      |
| Интерфейс пользователя                 | Latency                              | Время обработки запроса (целевое — до 5 секунд)                                                |

 - **Модели на основе спутниковых данных**

| Назначение                          | Метрика              | Комментарий                                                                 |
|-------------------------------------|----------------------|-----------------------------------------------------------------------------|
| Прогноз урожайности                 | R²                   | Объясняет дисперсию фактической урожайности                                 |
| Точность прогноза                   | RMSE, MAPE           | Абсолютные и относительные ошибки в т/га и % соответственно                 |
| Корреляция с индексами вегетации    | NDVI correlation     | Согласованность модели с динамикой NDVI                                     |
| Оповещения о риске                  | Precision / Recall   | Качество бинарной классификации «есть/нет угроза»                           |

---

 - **Критерии успеха**

| Сценарий использования                  | Метрика               | Минимум для запуска        | Оптимальное значение      |
|-----------------------------------------|-----------------------|----------------------------|---------------------------|
| Определение культуры по фото            | Accuracy, F1-score    | ≥ 90% accuracy (F1 ≥ 0.90) | ~98% accuracy (F1 ~0.98)  |
| Распознавание стадии роста              | Accuracy, F1-score    | ≥ 85% accuracy (F1 ≥ 0.85) | ≥ 95% accuracy (F1 ≥0.95) |
| Диагностика наличия и типа повреждения  | Accuracy, F1-score    | ≥ 80% accuracy (F1 ≥ 0.80) | ≥ 90% accuracy (F1 ≥0.95) |
| Сегментация повреждений (по фото)       | mIoU                  | ≥ 0.50                     | ≥ 0.70                    |
| Прогноз урожайности                     | R²                    | ≥ 0.70                     | ≥ 0.90                    |
| Ошибка прогноза урожайности             | MAPE                  | ≤ 15%                      | ≤ 5%                      |



### 1.3 План проекта (Project Plan)   

 - Бизнес-анализ (Business Understanding) - 1,5 недели.
 - Анализ данных (Data Understanding) - 1 неделя.
 - Подготовка данных (Data Preparation) - 1 неделя.
 - Моделирование (Modeling) - 1 неделя.
 - Оценка результата (Evaluation) - 2 дня.
 - Внедрение (Deployment) - 1 неделя.
