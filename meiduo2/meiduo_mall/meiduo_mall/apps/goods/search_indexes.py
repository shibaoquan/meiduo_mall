from haystack import indexes

from .models import SKU


class SKUIndex(indexes.SearchIndex, indexes.Indexable):

    """
    SKU索引数据模型类
    """

    text = indexes.CharField(document=True, use_template=True)
    id = indexes.IntegerField(model_attr='id')
    name = indexes.CharField(model_attr='name')
    price = indexes.DecimalField(model_attr='price')
    default_image_url = indexes.CharField(model_attr='default_image_url')
    comments = indexes.IntegerField(model_attr='comments')

    def get_model(self):
        """返回建立索引的模型类"""
        return SKU

    def index_queryset(self, using=None):
        """返回要建立索引的数据查询集"""
        return self.get_model().objects.filter(is_launched=True)

    """
        在SKUIndex建立的字段，都可以借助haystack由elasticsearch搜索引擎查询。
        其中text字段我们声明为document=True，表名该字段是主要进行关键字查询的字段，
         该字段的索引值可以由多个数据库模型类字段组成，具体由哪些模型类字段组成，
         我们用use_template=True表示后续通过模板来指明。其他字段都是通过model_attr
         选项指明引用数据库模型类的特定字段。
  
    """
