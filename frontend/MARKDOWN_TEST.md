# Markdown Rendering Test

This file contains various markdown elements to test the MessageContent component.

## Features to Test

### 1. Headers
Different levels of headers:

# H1 Header
## H2 Header
### H3 Header
#### H4 Header
##### H5 Header
###### H6 Header

### 2. Text Formatting

**Bold text** and *italic text* and ***bold italic***

Regular paragraph with some text. This should have proper spacing and line breaks.

Another paragraph to test spacing between blocks.

### 3. Lists

Unordered list:
- Item 1
- Item 2
  - Nested item 2.1
  - Nested item 2.2
- Item 3

Ordered list:
1. First item
2. Second item
3. Third item
   1. Nested 3.1
   2. Nested 3.2

### 4. Code Blocks

#### Python Code (should show language badge, copy button, line numbers)

\`\`\`python
def calculate_fibonacci(n):
    """Calculate the nth Fibonacci number using dynamic programming."""
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    
    fib = [0] * (n + 1)
    fib[1] = 1
    
    for i in range(2, n + 1):
        fib[i] = fib[i - 1] + fib[i - 2]
    
    return fib[n]

# Test the function
for i in range(10):
    print(f"F({i}) = {calculate_fibonacci(i)}")
\`\`\`

#### JavaScript Code

\`\`\`javascript
async function fetchData(url) {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching data:', error);
    throw error;
  }
}

// Usage
fetchData('https://api.example.com/data')
  .then(data => console.log(data))
  .catch(err => console.error(err));
\`\`\`

#### Long Code Block (should have expand/collapse)

\`\`\`typescript
interface User {
  id: number;
  username: string;
  email: string;
  created_at: Date;
}

class UserService {
  private users: Map<number, User> = new Map();
  private nextId: number = 1;

  createUser(username: string, email: string): User {
    const user: User = {
      id: this.nextId++,
      username,
      email,
      created_at: new Date()
    };
    this.users.set(user.id, user);
    return user;
  }

  getUserById(id: number): User | undefined {
    return this.users.get(id);
  }

  getAllUsers(): User[] {
    return Array.from(this.users.values());
  }

  updateUser(id: number, updates: Partial<User>): User | null {
    const user = this.users.get(id);
    if (!user) return null;
    
    const updatedUser = { ...user, ...updates };
    this.users.set(id, updatedUser);
    return updatedUser;
  }

  deleteUser(id: number): boolean {
    return this.users.delete(id);
  }
}

// Example usage
const service = new UserService();
const user1 = service.createUser('alice', 'alice@example.com');
const user2 = service.createUser('bob', 'bob@example.com');
console.log(service.getAllUsers());
\`\`\`

#### SQL Code

\`\`\`sql
SELECT 
  u.id,
  u.username,
  COUNT(p.id) as post_count,
  MAX(p.created_at) as last_post_date
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
WHERE u.active = true
GROUP BY u.id, u.username
HAVING COUNT(p.id) > 5
ORDER BY post_count DESC
LIMIT 10;
\`\`\`

#### Bash Script

\`\`\`bash
#!/bin/bash

# Backup script
BACKUP_DIR="/backup"
SOURCE_DIR="/data"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backup_${DATE}.tar.gz"

echo "Starting backup at $(date)"
tar -czf "${BACKUP_DIR}/${BACKUP_FILE}" "${SOURCE_DIR}"

if [ $? -eq 0 ]; then
  echo "Backup completed successfully"
else
  echo "Backup failed" >&2
  exit 1
fi
\`\`\`

### 5. Inline Code

Use the \`useState\` hook to manage state. Call \`npm install\` to install dependencies.

The API endpoint is \`/api/messages/search\` and it returns \`application/json\`.

### 6. Blockquotes

> This is a blockquote. It should have a left border and different background.
>
> Multiple paragraphs in a blockquote work too.

> **Note:** Important information can be emphasized in blockquotes.

### 7. Links

Visit [OpenRouter](https://openrouter.ai) for LLM access.

Check the [GitHub repository](https://github.com) for more information.

### 8. Tables

| Feature | Status | Priority |
|---------|--------|----------|
| Markdown rendering | ✅ Complete | High |
| Syntax highlighting | ✅ Complete | High |
| Copy buttons | ✅ Complete | High |
| Language badges | ✅ Complete | Medium |
| Expand/collapse | ✅ Complete | Medium |

### 9. Horizontal Rule

Content above the line

---

Content below the line

### 10. Mixed Content

Here's a complex example with **bold text**, *italic text*, `inline code`, and a [link](https://example.com).

\`\`\`python
def greet(name):
    return f"Hello, {name}!"
\`\`\`

- List item with **bold**
- List item with \`code\`
- List item with [link](https://example.com)

## Testing Instructions

1. Copy this entire content
2. Paste it as a message in the Chat tab
3. Verify all features render correctly:
   - ✅ Headers (H1-H6)
   - ✅ Bold, italic text
   - ✅ Lists (ordered, unordered, nested)
   - ✅ Code blocks with syntax highlighting
   - ✅ Language badges on code blocks
   - ✅ Copy buttons on code blocks
   - ✅ Line numbers on code blocks (>3 lines)
   - ✅ Expand/collapse on long code blocks (>15 lines)
   - ✅ Inline code styling
   - ✅ Blockquotes
   - ✅ Links (open in new tab)
   - ✅ Tables
   - ✅ Horizontal rules

## Code Block Edge Cases

Empty code block:
\`\`\`

\`\`\`

Code without language:
\`\`\`
plain text code
no syntax highlighting
\`\`\`

Short code (should NOT have expand/collapse):
\`\`\`python
print("Hello")
print("World")
\`\`\`
