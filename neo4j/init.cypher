CREATE CONSTRAINT course_id IF NOT EXISTS FOR (c:Course) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT knowledge_id IF NOT EXISTS FOR (k:KnowledgePoint) REQUIRE k.id IS UNIQUE;
CREATE CONSTRAINT clc_code IF NOT EXISTS FOR (c:CLCClass) REQUIRE c.code IS UNIQUE;
CREATE CONSTRAINT dimension_id IF NOT EXISTS FOR (d:DimensionValue) REQUIRE d.id IS UNIQUE;

UNWIND [
  {
    id: 'COURSE_INFO_ORGANIZATION',
    name: '信息组织',
    code: '07000030A',
    credits: 3,
    course_type: '平台/菜单',
    summary: '围绕分类法、主题词表、元数据和本体组织信息资源。',
    source: '南京大学信息管理学院公开课表与课程作业整理',
    clc_code: 'G254',
    clc_name: '文献标引与编目',
    dimensions: [
      {dimension: '文化', value: '知识组织文化'},
      {dimension: '机构', value: '图书馆与知识服务机构'},
      {dimension: '个人', value: '知识组织员'},
      {dimension: '计算', value: '本体与知识图谱'}
    ]
  },
  {
    id: 'COURSE_INFO_RETRIEVAL',
    name: '信息检索',
    code: '',
    credits: 3,
    course_type: '菜单',
    summary: '讨论用户需求、检索表达、搜索引擎和相关性排序。',
    source: '南京大学信息管理学院公开课表与课程作业整理',
    clc_code: 'G252.7',
    clc_name: '情报检索',
    dimensions: [
      {dimension: '文化', value: '信息素养文化'},
      {dimension: '机构', value: '数字图书馆平台'},
      {dimension: '个人', value: '信息用户'},
      {dimension: '计算', value: '搜索与排序算法'}
    ]
  },
  {
    id: 'COURSE_DATA_STRUCTURE',
    name: '数据结构',
    code: '07020020',
    credits: 3,
    course_type: '核心',
    summary: '学习抽象数据类型、线性结构、树、图和算法复杂度。',
    source: '南京大学信息管理学院公开课表与课程作业整理',
    clc_code: 'TP311.12',
    clc_name: '数据结构',
    dimensions: [
      {dimension: '文化', value: '计算思维文化'},
      {dimension: '机构', value: '软件研发组织'},
      {dimension: '个人', value: '系统开发者'},
      {dimension: '计算', value: '数据结构与算法'}
    ]
  },
  {
    id: 'COURSE_DATA_SCIENCE',
    name: '数据科学与数据分析',
    code: '07020460',
    credits: 6,
    course_type: '核心',
    summary: '围绕数据清洗、统计分析、建模、机器学习和可视化展开。',
    source: '南京大学信息管理学院公开课表与课程作业整理',
    clc_code: 'TP274',
    clc_name: '数据处理',
    dimensions: [
      {dimension: '文化', value: '数据驱动文化'},
      {dimension: '机构', value: '数据分析部门'},
      {dimension: '个人', value: '数据分析师'},
      {dimension: '计算', value: '机器学习与分析'}
    ]
  },
  {
    id: 'COURSE_MIS',
    name: '管理信息系统',
    code: '07020480',
    credits: 3,
    course_type: '核心',
    summary: '从管理流程、系统分析、数据库和决策支持理解组织中的信息系统。',
    source: '南京大学信息管理学院公开课表与课程作业整理',
    clc_code: 'C931.6',
    clc_name: '管理信息系统',
    dimensions: [
      {dimension: '文化', value: '组织管理文化'},
      {dimension: '机构', value: '企业信息部门'},
      {dimension: '个人', value: '系统分析师'},
      {dimension: '计算', value: '数据库与业务系统'}
    ]
  },
  {
    id: 'COURSE_INFO_ANALYSIS',
    name: '信息分析',
    code: '07000050',
    credits: 3,
    course_type: '平台',
    summary: '面向文本、舆情、指标体系和统计方法组织分析流程。',
    source: '南京大学信息管理学院公开课表与课程作业整理',
    clc_code: 'G350',
    clc_name: '情报学',
    dimensions: [
      {dimension: '文化', value: '证据推理文化'},
      {dimension: '机构', value: '情报分析机构'},
      {dimension: '个人', value: '信息分析师'},
      {dimension: '计算', value: '文本挖掘与可视化'}
    ]
  }
] AS row
MERGE (course:Course {id: row.id})
SET course.name = row.name,
    course.code = row.code,
    course.credits = row.credits,
    course.course_type = row.course_type,
    course.summary = row.summary,
    course.source = row.source
MERGE (clc:CLCClass {code: row.clc_code})
SET clc.id = 'CLC_' + row.clc_code,
    clc.name = row.clc_name
MERGE (course)-[:CLASSIFIED_BY]->(clc)
WITH row, course
UNWIND row.dimensions AS dim
MERGE (value:DimensionValue {id: row.id + '_' + dim.dimension + '_' + dim.value})
SET value.dimension = dim.dimension,
    value.value = dim.value,
    value.name = dim.value
MERGE (course)-[:HAS_DIMENSION {dimension: dim.dimension}]->(value);

UNWIND [
  {id: 'KP_KNOWLEDGE_ORGANIZATION', name: '知识组织'},
  {id: 'KP_THESAURUS', name: '主题词表'},
  {id: 'KP_SUBJECT_INDEXING', name: '主题标引'},
  {id: 'KP_CLASSIFICATION', name: '分类法'},
  {id: 'KP_METADATA', name: '元数据'},
  {id: 'KP_ONTOLOGY', name: '本体'},
  {id: 'KP_INFORMATION_RETRIEVAL', name: '信息检索'},
  {id: 'KP_SEARCH_ENGINE', name: '搜索引擎'},
  {id: 'KP_BOOLEAN_RETRIEVAL', name: '布尔检索'},
  {id: 'KP_RELEVANCE_RANKING', name: '相关性排序'},
  {id: 'KP_USER_NEED', name: '信息需求'},
  {id: 'KP_ABSTRACT_DATA_TYPE', name: '抽象数据类型'},
  {id: 'KP_LINEAR_LIST', name: '线性表'},
  {id: 'KP_TREE_STRUCTURE', name: '树结构'},
  {id: 'KP_GRAPH_STRUCTURE', name: '图结构'},
  {id: 'KP_ALGORITHM_COMPLEXITY', name: '算法复杂度'},
  {id: 'KP_DATA_CLEANING', name: '数据清洗'},
  {id: 'KP_DATA_MODELING', name: '数据建模'},
  {id: 'KP_MACHINE_LEARNING', name: '机器学习'},
  {id: 'KP_STATISTICAL_ANALYSIS', name: '统计分析'},
  {id: 'KP_DATA_VISUALIZATION', name: '数据可视化'},
  {id: 'KP_INFORMATION_SYSTEM', name: '信息系统'},
  {id: 'KP_BUSINESS_PROCESS', name: '业务流程'},
  {id: 'KP_SYSTEM_ANALYSIS', name: '系统分析'},
  {id: 'KP_DATABASE', name: '数据库'},
  {id: 'KP_DECISION_SUPPORT', name: '决策支持'},
  {id: 'KP_INFORMATION_ANALYSIS', name: '信息分析'},
  {id: 'KP_TEXT_MINING', name: '文本挖掘'},
  {id: 'KP_PUBLIC_OPINION', name: '网络舆情'},
  {id: 'KP_INDICATOR_SYSTEM', name: '指标体系'}
] AS row
MERGE (kp:KnowledgePoint {id: row.id})
SET kp.name = row.name,
    kp.source = '《汉语主题词表》主题词粒度整理';

UNWIND [
  {course_id: 'COURSE_INFO_ORGANIZATION', knowledge_id: 'KP_KNOWLEDGE_ORGANIZATION'},
  {course_id: 'COURSE_INFO_ORGANIZATION', knowledge_id: 'KP_THESAURUS'},
  {course_id: 'COURSE_INFO_ORGANIZATION', knowledge_id: 'KP_SUBJECT_INDEXING'},
  {course_id: 'COURSE_INFO_ORGANIZATION', knowledge_id: 'KP_CLASSIFICATION'},
  {course_id: 'COURSE_INFO_ORGANIZATION', knowledge_id: 'KP_METADATA'},
  {course_id: 'COURSE_INFO_ORGANIZATION', knowledge_id: 'KP_ONTOLOGY'},
  {course_id: 'COURSE_INFO_RETRIEVAL', knowledge_id: 'KP_INFORMATION_RETRIEVAL'},
  {course_id: 'COURSE_INFO_RETRIEVAL', knowledge_id: 'KP_SEARCH_ENGINE'},
  {course_id: 'COURSE_INFO_RETRIEVAL', knowledge_id: 'KP_BOOLEAN_RETRIEVAL'},
  {course_id: 'COURSE_INFO_RETRIEVAL', knowledge_id: 'KP_RELEVANCE_RANKING'},
  {course_id: 'COURSE_INFO_RETRIEVAL', knowledge_id: 'KP_USER_NEED'},
  {course_id: 'COURSE_INFO_RETRIEVAL', knowledge_id: 'KP_THESAURUS'},
  {course_id: 'COURSE_DATA_STRUCTURE', knowledge_id: 'KP_ABSTRACT_DATA_TYPE'},
  {course_id: 'COURSE_DATA_STRUCTURE', knowledge_id: 'KP_LINEAR_LIST'},
  {course_id: 'COURSE_DATA_STRUCTURE', knowledge_id: 'KP_TREE_STRUCTURE'},
  {course_id: 'COURSE_DATA_STRUCTURE', knowledge_id: 'KP_GRAPH_STRUCTURE'},
  {course_id: 'COURSE_DATA_STRUCTURE', knowledge_id: 'KP_ALGORITHM_COMPLEXITY'},
  {course_id: 'COURSE_DATA_SCIENCE', knowledge_id: 'KP_DATA_CLEANING'},
  {course_id: 'COURSE_DATA_SCIENCE', knowledge_id: 'KP_DATA_MODELING'},
  {course_id: 'COURSE_DATA_SCIENCE', knowledge_id: 'KP_MACHINE_LEARNING'},
  {course_id: 'COURSE_DATA_SCIENCE', knowledge_id: 'KP_STATISTICAL_ANALYSIS'},
  {course_id: 'COURSE_DATA_SCIENCE', knowledge_id: 'KP_DATA_VISUALIZATION'},
  {course_id: 'COURSE_MIS', knowledge_id: 'KP_INFORMATION_SYSTEM'},
  {course_id: 'COURSE_MIS', knowledge_id: 'KP_BUSINESS_PROCESS'},
  {course_id: 'COURSE_MIS', knowledge_id: 'KP_SYSTEM_ANALYSIS'},
  {course_id: 'COURSE_MIS', knowledge_id: 'KP_DATABASE'},
  {course_id: 'COURSE_MIS', knowledge_id: 'KP_DECISION_SUPPORT'},
  {course_id: 'COURSE_MIS', knowledge_id: 'KP_METADATA'},
  {course_id: 'COURSE_INFO_ANALYSIS', knowledge_id: 'KP_INFORMATION_ANALYSIS'},
  {course_id: 'COURSE_INFO_ANALYSIS', knowledge_id: 'KP_TEXT_MINING'},
  {course_id: 'COURSE_INFO_ANALYSIS', knowledge_id: 'KP_PUBLIC_OPINION'},
  {course_id: 'COURSE_INFO_ANALYSIS', knowledge_id: 'KP_INDICATOR_SYSTEM'},
  {course_id: 'COURSE_INFO_ANALYSIS', knowledge_id: 'KP_STATISTICAL_ANALYSIS'},
  {course_id: 'COURSE_INFO_ANALYSIS', knowledge_id: 'KP_DATA_VISUALIZATION'}
] AS row
MATCH (course:Course {id: row.course_id})
MATCH (kp:KnowledgePoint {id: row.knowledge_id})
MERGE (course)-[:HAS_KNOWLEDGE_POINT {source: '课程知识点'}]->(kp);

UNWIND [
  {source: 'KP_KNOWLEDGE_ORGANIZATION', target: 'KP_THESAURUS', relation: '下位词'},
  {source: 'KP_KNOWLEDGE_ORGANIZATION', target: 'KP_CLASSIFICATION', relation: '下位词'},
  {source: 'KP_KNOWLEDGE_ORGANIZATION', target: 'KP_METADATA', relation: '相关词'},
  {source: 'KP_KNOWLEDGE_ORGANIZATION', target: 'KP_ONTOLOGY', relation: '相关词'},
  {source: 'KP_THESAURUS', target: 'KP_SUBJECT_INDEXING', relation: '相关词'},
  {source: 'KP_INFORMATION_RETRIEVAL', target: 'KP_BOOLEAN_RETRIEVAL', relation: '下位词'},
  {source: 'KP_INFORMATION_RETRIEVAL', target: 'KP_RELEVANCE_RANKING', relation: '相关词'},
  {source: 'KP_INFORMATION_RETRIEVAL', target: 'KP_USER_NEED', relation: '相关词'},
  {source: 'KP_SEARCH_ENGINE', target: 'KP_RELEVANCE_RANKING', relation: '相关词'},
  {source: 'KP_ABSTRACT_DATA_TYPE', target: 'KP_LINEAR_LIST', relation: '下位词'},
  {source: 'KP_ABSTRACT_DATA_TYPE', target: 'KP_TREE_STRUCTURE', relation: '下位词'},
  {source: 'KP_ABSTRACT_DATA_TYPE', target: 'KP_GRAPH_STRUCTURE', relation: '下位词'},
  {source: 'KP_GRAPH_STRUCTURE', target: 'KP_ONTOLOGY', relation: '相关词'},
  {source: 'KP_DATA_MODELING', target: 'KP_MACHINE_LEARNING', relation: '相关词'},
  {source: 'KP_STATISTICAL_ANALYSIS', target: 'KP_DATA_VISUALIZATION', relation: '相关词'},
  {source: 'KP_INFORMATION_SYSTEM', target: 'KP_DATABASE', relation: '组成部分'},
  {source: 'KP_INFORMATION_SYSTEM', target: 'KP_BUSINESS_PROCESS', relation: '相关词'},
  {source: 'KP_SYSTEM_ANALYSIS', target: 'KP_BUSINESS_PROCESS', relation: '相关词'},
  {source: 'KP_INFORMATION_ANALYSIS', target: 'KP_TEXT_MINING', relation: '下位词'},
  {source: 'KP_INFORMATION_ANALYSIS', target: 'KP_INDICATOR_SYSTEM', relation: '相关词'},
  {source: 'KP_TEXT_MINING', target: 'KP_PUBLIC_OPINION', relation: '应用领域'}
] AS row
MATCH (source:KnowledgePoint {id: row.source})
MATCH (target:KnowledgePoint {id: row.target})
MERGE (source)-[rel:KNOWLEDGE_RELATION {relation: row.relation}]->(target);

