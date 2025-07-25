import os
import sys
import argparse
from typing import List
from rag_manager import RAGManager
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
    '..')))


def create_sample_data() ->List[str]:
    """Create sample documents for the RAG example."""
    return [
        'RAG stands for Retrieval-Augmented Generation, a technique that combines information retrieval with language generation.'
        ,
        'The RAG model retrieves relevant documents from a knowledge base and uses them to generate more accurate responses.'
        ,
        'FAISS is a library for efficient similarity search and clustering of dense vectors, often used in RAG systems.'
        ,
        'Sentence transformers are used to create embeddings for documents and queries in RAG systems.'
        ,
        'Retrieval-Augmented Generation improves language models by allowing them to access external knowledge sources.'
        ,
        'In RAG systems, documents are indexed and searchable by their semantic embeddings rather than just keywords.'
        ,
        'Python is a great language for implementing RAG systems due to libraries like sentence-transformers and faiss.'
        ,
        'The retrieval component of RAG is crucial for finding relevant information before generation.'
        ]


def main():
    """Main function demonstrating RAG through CLI."""
    parser = argparse.ArgumentParser(description='RAG CLI Example')
    parser.add_argument('--query', '-q', type=str, help='Query to search for')
    parser.add_argument('--add', '-a', type=str, help=
        'Add a new document to the index')
    parser.add_argument('--list', '-l', action='store_true', help=
        'List all documents in the index')
    parser.add_argument('--clear', '-c', action='store_true', help=
        'Clear the index')
    parser.add_argument('--init', '-i', action='store_true', help=
        'Initialize with sample data')
    args = parser.parse_args()
    rag_manager = RAGManager()
    if args.clear:
        rag_manager.clear_index()
        print('Index cleared.')
        return
    if args.init:
        documents = create_sample_data()
        rag_manager.add_documents(documents)
        print(f'Added {len(documents)} sample documents to index.')
        return
    if args.add:
        rag_manager.add_documents([args.add])
        print(f'Added document: {args.add}')
        return
    if args.list:
        if rag_manager.get_document_count() == 0:
            print(
                'No documents in index. Use --init to add sample data or --add to add documents.'
                )
        else:
            print(
                f'Documents in index ({rag_manager.get_document_count()} total):'
                )
            for i, meta in enumerate(rag_manager.metadata):
                print(f"  {i + 1}. {meta['content']}")
        return
    if args.query:
        if rag_manager.get_document_count() == 0:
            print(
                'Index is empty. Use --init to add sample data or --add to add documents.'
                )
            return
        results = rag_manager.search(args.query, k=3)
        print(f"Top 3 results for '{args.query}':")
        for i, (doc, score, meta) in enumerate(results, 1):
            print(f'  {i}. [Score: {score:.4f}] {doc}')
        return
    parser.print_help()


def main():
    """Main function demonstrating RAG through CLI."""
    parser = argparse.ArgumentParser(description='RAG CLI Example')
    parser.add_argument('--query', '-q', type=str, help='Query to search for')
    parser.add_argument('--add', '-a', type=str, help=
        'Add a new document to the index')
    parser.add_argument('--list', '-l', action='store_true', help=
        'List all documents in the index')
    parser.add_argument('--clear', '-c', action='store_true', help=
        'Clear the index')
    parser.add_argument('--init', '-i', action='store_true', help=
        'Initialize with sample data')
    args = parser.parse_args()
    rag_manager = RAGManager()
    if args.clear:
        rag_manager.clear_index()
        print('Index cleared.')
        return
    if args.init:
        documents = create_sample_data()
        rag_manager.add_documents(documents)
        print(f'Added {len(documents)} sample documents to index.')
        return
    if args.add:
        rag_manager.add_documents([args.add])
        print(f'Added document: {args.add}')
        return
    if args.list:
        if rag_manager.get_document_count() == 0:
            print(
                'No documents in index. Use --init to add sample data or --add to add documents.'
                )
        else:
            print(
                f'Documents in index ({rag_manager.get_document_count()} total):'
                )
            for i, meta in enumerate(rag_manager.metadata):
                print(f"  {i + 1}. {meta['content']}")
        return
    if args.query:
        if rag_manager.get_document_count() == 0:
            print(
                'Index is empty. Use --init to add sample data or --add to add documents.'
                )
            return
        results = rag_manager.search(args.query, k=3)
        print(f"Top 3 results for '{args.query}':")
        for i, (doc, score, meta) in enumerate(results, 1):
            print(f'  {i}. [Score: {score:.4f}] {doc}')
        return
    parser.print_help()


if __name__ == '__main__':
    main()
