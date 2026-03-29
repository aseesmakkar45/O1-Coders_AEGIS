def main():
    path = "c:/Users/anush/Downloads/rosetta (2)/rosetta/frontend/index.html"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    content = content.replace("8000", "8001")
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    main()
