/**
 * Simple markdown parser for HiRA responses
 * Handles bold, italic, and line breaks
 */

export function parseMarkdown(text) {
  if (!text) return '';

  // Replace **bold** with <strong>
  text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

  // Replace *italic* with <em>
  text = text.replace(/\*(.+?)\*/g, '<em>$1</em>');

  // Replace newlines with <br>
  text = text.replace(/\n/g, '<br>');

  return text;
}
