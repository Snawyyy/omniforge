import os
import sys
from typing import List
"""
Example script demonstrating RAG (Retrieval-Augmented Generation) usage.

This script shows how to use a simple RAG implementation to answer questions
based on a given context or knowledge base.
"""
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
    '..')))


class SimpleRAG:
    """A simple RAG implementation for demonstration purposes."""

    def __init__(self, knowledge_base: List[str]):
        """
        Initialize the RAG with a knowledge base.
        
        Args:
            knowledge_base: A list of strings representing the knowledge base.
        """
        self.knowledge_base = knowledge_base

    def retrieve(self, query: str, top_k: int=3) ->List[str]:
        """
        Retrieve relevant documents from the knowledge base.
        
        This is a simplified implementation using keyword matching.
        In a real implementation, you would use embeddings and vector search.
        
        Args:
            query: The query string.
            top_k: Number of top documents to retrieve.
            
        Returns:
            A list of relevant documents.
        """
        query_words = set(query.lower().split())
        scores = []
        for doc in self.knowledge_base:
            doc_words = set(doc.lower().split())
            score = len(query_words.intersection(doc_words))
            scores.append((score, doc))
        scores.sort(reverse=True)
        return [doc for score, doc in scores[:top_k]]

    def generate(self, query: str, retrieved_docs: List[str]) ->str:
        """
        Generate an answer based on the query and retrieved documents.
        
        In a real implementation, this would use an LLM to generate the response.
        For this example, we'll create a simple template-based response.
        
        Args:
            query: The query string.
            retrieved_docs: The retrieved documents.
            
        Returns:
            A generated answer.
        """
        context = '\n'.join(retrieved_docs)
        prompt = f"""
        Context information:
        {context}
        
        Question: {query}
        
        Based on the context provided above, please answer the question.
        If the context doesn't contain relevant information, say so.
        """
        return self._simple_response_generator(query, retrieved_docs)

    def _simple_response_generator(self, query: str, retrieved_docs: List[str]
        ) ->str:
        """
        A simple response generator for demonstration.
        """
        for doc in retrieved_docs:
            if 'example' in doc.lower():
                return (
                    f'Based on the context provided, I found information about examples. {query} relates to the examples in the knowledge base.'
                    )
        return (
            f"I couldn't find specific information about '{query}' in the provided context. Please provide more details or check the knowledge base."
            )

    def query(self, query: str, top_k: int=3) ->str:
        """
        Process a query through the full RAG pipeline.
        
        Args:
            query: The query string.
            top_k: Number of top documents to retrieve.
            
        Returns:
            The generated answer.
        """
        retrieved_docs = self.retrieve(query, top_k)
        answer = self.generate(query, retrieved_docs)
        return answer


def main():
    """Main function demonstrating the RAG implementation."""
    knowledge_base = ['This is an example document about machine learning.',
        'Natural language processing is a subfield of artificial intelligence.'
        , 'Python is a popular programming language for data science.',
        'The quick brown fox jumps over the lazy dog.',
        'RAG stands for Retrieval-Augmented Generation.',
        'Vector databases are used for similarity search in RAG systems.',
        'Transformers are a type of neural network architecture.',
        'This example shows how to implement a simple RAG system.']
    rag = SimpleRAG(knowledge_base)
    queries = ['What is RAG?', 'How is Python used in data science?',
        'Tell me about machine learning']
    print('Simple RAG Example')
    print('=' * 50)
    for query in queries:
        print(f'\nQuery: {query}')
        answer = rag.query(query)
        print(f'Answer: {answer}')
        print('-' * 30)
    print("\nInteractive Mode (type 'quit' to exit):")
    while True:
        try:
            user_query = input('\nEnter your question: ').strip()
            if user_query.lower() in ['quit', 'exit', 'q']:
                break
            if user_query:
                answer = rag.query(user_query)
                print(f'Answer: {answer}')
        except KeyboardInterrupt:
            print('\nGoodbye!')
            break
        except EOFError:
            break


if __name__ == '__main__':
    main()
