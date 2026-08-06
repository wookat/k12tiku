DROP TABLE IF EXISTS q;
CREATE TABLE q(
  id INTEGER PRIMARY KEY,
  stage TEXT, grade TEXT, subject TEXT, qtype TEXT, difficulty TEXT,
  question TEXT, answer TEXT, explanation TEXT, source TEXT
);
CREATE INDEX idx_q_stage_subject ON q(stage, subject);
DROP TABLE IF EXISTS q_fts;
CREATE VIRTUAL TABLE q_fts USING fts5(question, content='q', content_rowid='id', tokenize='trigram');
