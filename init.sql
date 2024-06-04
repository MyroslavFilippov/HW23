CREATE TABLE books (
  id BIGINT NOT NULL,
  category_id INT NOT NULL,
  author VARCHAR NOT NULL,
  title VARCHAR NOT NULL,
  year INT NOT NULL,
  last_modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Function to update last_modified column
CREATE OR REPLACE FUNCTION update_last_modified()
RETURNS TRIGGER AS $$
BEGIN
  NEW.last_modified = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update last_modified column on update
CREATE TRIGGER update_books_last_modified
BEFORE UPDATE ON books
FOR EACH ROW
EXECUTE FUNCTION update_last_modified();

-- Function to notify changes
CREATE OR REPLACE FUNCTION notify_books_changes()
RETURNS TRIGGER AS $$
BEGIN
  PERFORM pg_notify('books_changes', row_to_json(NEW)::text);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to notify changes on insert or update
CREATE TRIGGER books_changes_notify
AFTER INSERT OR UPDATE ON books
FOR EACH ROW
EXECUTE FUNCTION notify_books_changes();
