# DeepHtmlExtract

## 项目概述

DeepHtmlExtract 是一个基于Python的工具，旨在从网页中自动提取主要内容。它使用机器学习技术来识别和提取文章的核心内容，包括标题、作者、日期、主要文本和图片。

## 主要特性

- 使用机器学习模型识别主要内容
- 提取文章标题、作者和日期信息
- 识别和提取文章中的图片
- 将提取的内容格式化为Markdown格式
- 支持模型的保存和加载，便于重复使用

## 技术栈

- Python 3.x
- requests: 用于下载网页
- BeautifulSoup4: 用于解析HTML
- scikit-learn: 提供机器学习功能
- pickle: 用于保存和加载模型

## 安装

1. 克隆此仓库：
   ```
   git clone https://github.com/Gloridust/DeepHtmlExtract.git
   cd DeepHtmlExtract
   ```

2. 安装所需的Python包：
   ```
   pip install requests beautifulsoup4 scikit-learn
   ```

## 使用方法

1. 首先，训练模型：
   ```
   python train_extractor.py
   ```
   这将使用 `training_data.json` 中的数据训练模型，并将模型保存为 `vectorizer.pkl` 和 `classifier.pkl`。

2. 然后，使用训练好的模型提取内容：
   ```
   python use_extractor.py
   ```
   默认情况下，这将从 `https://example.com/article` 提取内容。你可以在 `use_extractor.py` 文件中修改URL。

## 文件结构

- `html_content_extractor.py`: 主要的类和函数定义
- `train_extractor.py`: 用于训练模型的脚本
- `use_extractor.py`: 使用训练好的模型提取内容的脚本
- `training_data.json`: 包含训练数据的JSON文件

## 自定义

- 你可以通过修改 `training_data.json` 文件来添加更多的训练数据。
- 在 `html_content_extractor.py` 中，你可以调整内容提取的逻辑，以适应不同的网页结构。

## 注意事项

- 这个项目仅用于教育和研究目的。在使用时，请确保遵守网站的使用条款和robots.txt规则。
- 当前的实现比较简单，可能需要根据具体的网站结构进行调整。
- 在生产环境中使用时，建议添加更robust的错误处理和日志记录。

## 贡献

欢迎提交问题和拉取请求。对于重大更改，请先开issue讨论你想要改变的内容。

## 许可证

[MIT](https://choosealicense.com/licenses/mit/)