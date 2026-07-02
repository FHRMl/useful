# 课程知识图谱数据与本体设计

## 数据分工

Neo4j 存储相对稳定的图谱结构：课程、知识点、中图法分类节点、四类分类维度节点，以及课程-知识点、课程-分类、课程-维度、知识点-知识点关系。

MySQL 存储运行时动态数据：用户、课程评分点评、知识点个人标注。这样可以把需要频繁增删改查和权限控制的数据放在关系数据库中，把多跳关联查询和图谱可视化数据放在图数据库中。

## 核心类

| 类 | 说明 | 主要属性 |
| --- | --- | --- |
| Course | 信息管理学院课程 | id、name、code、credits、course_type、summary |
| KnowledgePoint | 课程知识点，按主题词粒度整理 | id、name、source |
| CLCClass | 中图法分类号节点 | code、name |
| DimensionValue | 文化、机构、个人、计算四类维度的具体取值 | id、dimension、value |
| User | 系统用户 | username、display_name、password_hash |
| CourseReview | 用户对课程的评分点评 | course_id、rating、comment |
| KnowledgeAnnotation | 用户对知识点的个人标注 | knowledge_id、note、visibility |

## 核心关系

| 关系 | 起点 | 终点 | 说明 |
| --- | --- | --- | --- |
| HAS_KNOWLEDGE_POINT | Course | KnowledgePoint | 课程包含知识点 |
| CLASSIFIED_BY | Course | CLCClass | 课程对应中图法分类号 |
| HAS_DIMENSION | Course | DimensionValue | 课程在四类分类维度上的赋值 |
| KNOWLEDGE_RELATION | KnowledgePoint | KnowledgePoint | 上位、下位、相关、组成、应用等主题词关系 |

## 本体约束

每门课程至少连接 5 个知识点，每个知识点使用课程作业要求中的《汉语主题词表》主题词粒度进行命名。课程节点必须给出中图法分类号，并必须连接文化、机构、个人、计算四类维度各一个取值。

运行时每个用户可以对多门课程评分点评，也可以对多个知识点添加公开或私有标注。课程评价通过 `(user_id, course_id)` 唯一约束保证一个用户对一门课程只有一条当前评价。

