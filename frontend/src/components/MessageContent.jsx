import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

const MAX_COLLAPSED_LINES = 15;

export default function MessageContent({ content, isStreaming = false }) {
  // Show raw text during streaming for performance
  if (isStreaming) {
    return <div className="message-content-raw">{content}</div>;
  }

  return (
    <div className="message-content">
      <ReactMarkdown
        components={{
          code({ node, inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '');
            const code = String(children).replace(/\n$/, '');
            
            if (inline) {
              return <code className="inline-code" {...props}>{children}</code>;
            }

            if (!match) {
              // Code block without language
              return (
                <CodeBlock
                  code={code}
                  language="text"
                  {...props}
                />
              );
            }

            return (
              <CodeBlock
                code={code}
                language={match[1]}
                {...props}
              />
            );
          },
          // Style other markdown elements
          h1: ({ children }) => <h1 className="md-h1">{children}</h1>,
          h2: ({ children }) => <h2 className="md-h2">{children}</h2>,
          h3: ({ children }) => <h3 className="md-h3">{children}</h3>,
          h4: ({ children }) => <h4 className="md-h4">{children}</h4>,
          h5: ({ children }) => <h5 className="md-h5">{children}</h5>,
          h6: ({ children }) => <h6 className="md-h6">{children}</h6>,
          p: ({ children }) => <p className="md-p">{children}</p>,
          ul: ({ children }) => <ul className="md-ul">{children}</ul>,
          ol: ({ children }) => <ol className="md-ol">{children}</ol>,
          li: ({ children }) => <li className="md-li">{children}</li>,
          blockquote: ({ children }) => <blockquote className="md-blockquote">{children}</blockquote>,
          a: ({ href, children }) => <a href={href} className="md-link" target="_blank" rel="noopener noreferrer">{children}</a>,
          table: ({ children }) => <div className="md-table-wrapper"><table className="md-table">{children}</table></div>,
          thead: ({ children }) => <thead className="md-thead">{children}</thead>,
          tbody: ({ children }) => <tbody className="md-tbody">{children}</tbody>,
          tr: ({ children }) => <tr className="md-tr">{children}</tr>,
          th: ({ children }) => <th className="md-th">{children}</th>,
          td: ({ children }) => <td className="md-td">{children}</td>,
          hr: () => <hr className="md-hr" />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

function CodeBlock({ code, language, ...props }) {
  const [isCopied, setIsCopied] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const lineCount = code.split('\n').length;
  const needsCollapse = lineCount > MAX_COLLAPSED_LINES;
  const shouldCollapse = needsCollapse && !isExpanded;

  const displayCode = shouldCollapse 
    ? code.split('\n').slice(0, MAX_COLLAPSED_LINES).join('\n')
    : code;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <div className="code-block-wrapper">
      <div className="code-header">
        <span className="language-badge">{language}</span>
        <div className="code-actions">
          {needsCollapse && (
            <button
              className="code-action-btn expand-btn"
              onClick={() => setIsExpanded(!isExpanded)}
              title={isExpanded ? 'Collapse' : 'Expand'}
            >
              {isExpanded ? '−' : '+'}
            </button>
          )}
          <button
            className="code-action-btn copy-btn"
            onClick={handleCopy}
            title="Copy code"
          >
            {isCopied ? '✓' : 'Copy'}
          </button>
        </div>
      </div>
      <div className={`code-content ${shouldCollapse ? 'collapsed' : ''}`}>
        <SyntaxHighlighter
          style={oneDark}
          language={language}
          PreTag="div"
          showLineNumbers={lineCount > 3}
          wrapLines={true}
          {...props}
        >
          {displayCode}
        </SyntaxHighlighter>
        {shouldCollapse && (
          <div className="code-fade">
            <button
              className="expand-overlay-btn"
              onClick={() => setIsExpanded(true)}
            >
              Show {lineCount - MAX_COLLAPSED_LINES} more lines
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
