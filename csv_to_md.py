import csv

def csv_to_md(csv_file, md_file):
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='|')
        with open(md_file, 'w', encoding='utf-8') as out:
            out.write("# Посты из @turboproject про GRACE\n\n")
            for row in reader:
                date = row['date']
                text = row['text'].replace('\n', '\n')
                out.write(f"## Дата: {date}\n\n")
                out.write(f"{text}\n\n")
                out.write("---\n\n")

if __name__ == "__main__":
    csv_to_md('GRACE_posts.csv', 'GRACE_posts.md')

