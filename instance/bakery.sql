INSERT INTO `user` (`id`, `username`, `email`, `password`, `role`, `created_at`) VALUES 
(1, 'chubenkodo@gmail.com', 'chubenkodo@gmail.com', 'scrypt:32768:8:1$2bDcTscDVdKOtpti$485ab45026264bbd5ddd85b5ef6e1809305eaaee2eac3b766e57387e21e0df0813c6cf8cc46038e609dacb5a9e197e940595baa7160649594c1e5715086735ed', 'admin', '2024-09-29 20:34:24'),
(2, 'Moder@gmail.com', 'Moder@gmail.com', 'scrypt:32768:8:1$7Xvqd9BAsFNCsOKe$241ef9b5d5fb1d006df0269e7da59c49e3a007a11dbc3a9f0a0de5c13d1dd5cfc93073d282b084b73ab1919bf5a4c370e62add499457ca27072f7bb2b39f95ef', 'moderator', '2024-09-30 16:34:42'),
(3, 'customer@gmail.com', 'customer@gmail.com', 'scrypt:32768:8:1$nsqa5F7syfstBK5D$bd308830d9fd4609043a7c493b7097247d7df93b770a6b641d01cb478b05811aede086427065da3972485ceaa3d9f2aa880cd92bb80f25b5050ded1741ac501c', 'customer', '2024-09-30 16:35:18');

INSERT INTO `Category` (`id`, `name`, `created_at`) VALUES 
(1, 'Хлебобулочные изделия', '2024-09-29 20:35:36'),
(2, 'Напитки', '2024-09-29 20:35:49'),
(3, 'Кондитерские изделия', '2024-09-30 16:25:35'),
(4, 'Пирожные', '2024-09-30 16:25:49'),
(5, 'Торты', '2024-09-30 16:25:59'),
(6, 'Закуски', '2024-09-30 16:26:08');

INSERT INTO `Product` (`id`, `name`, `description`, `price`, `category_id`, `image_path`, `created_at`) VALUES 
(1, 'Кола (Бавария)', 'Прохладный сильногазированный напиток', 87.0, 2, 'https://beershop161.ru/upload/iblock/800/pqnyu85ii5lxxeb3w89lx4j04evsrm8l.jpg', '2024-09-29 20:37:00'),
(2, 'Хлеб ржаной', 'Свежий ржаной хлеб, приготовленный по традиционному рецепту.', 50.0, 1, 'https://th.bing.com/th/id/R.ff89e1e86398edd861276aa75550a050?rik=3bM1Mz8%2b40QfYA&pid=ImgRaw&r=0', '2024-09-30 16:26:43'),
(3, 'Булочка с корицей', 'Нежная булочка с ароматной корицей и сахаром.', 36.0, 4, 'https://th.bing.com/th/id/OIP.HXJXYx1PNyWxQA63rBMQWAHaHa?pid=ImgDetMain', '2024-09-30 16:27:24'),
(4, 'Круассан', 'Восхитительный круассан с маслом, идеально подходит к утреннему кофе.', 40.0, 3, 'https://th.bing.com/th/id/R.2d7841d9d85b8dc9ff8cbf9ecc324f7f?rik=I%2fs9tDfXK5bZ%2fw&pid=ImgRaw&r=0', '2024-09-30 16:28:00'),
(5, 'Торт Наполеон', 'Классический торт с многослойным тестом и кремом.', 330.0, 5, 'https://th.bing.com/th/id/OIP.k9UyiK0JtdBTEPlXHLzyKwHaHa?pcl=1b1a19&pid=ImgDetMain', '2024-09-30 16:28:53'),
(6, 'Пирожок с яблоками', 'Сладкий пирожок с начинкой из свежих яблок.', 25.0, 4, 'https://th.bing.com/th/id/R.2c9b29c01bdc325ad919680e566fc448?rik=Kv7%2bqTfufTh86Q&pid=ImgRaw&r=0', '2024-09-30 16:29:21');

INSERT INTO `Purchase` (`id`, `user_id`, `created_at`, `status`) VALUES 
(1, 1, '2024-09-30 11:21:12', 'pending'),
(2, 1, '2024-09-30 16:39:56', 'pending');

INSERT INTO `Cart_item` (`id`, `cart_id`, `product_id`, `quantity`) VALUES 
(1, NULL, 1, 2),
(2, NULL, 3, 2),
(3, NULL, 4, 1);

INSERT INTO `Purchase_item` (`id`, `purchase_id`, `product_id`, `quantity`, `cart_id`) VALUES 
(1, 1, 1, 2, 1),
(2, 2, 3, 2, 1),
(3, 2, 4, 1, 1);
