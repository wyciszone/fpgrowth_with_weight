from collections import defaultdict, Counter
import pandas as pd

class FPNode:
    def __init__(self, item, count=0):
        self.item = item
        self.count = count
        self.parent = None
        self.children = {}
        self.link = None

    def increment(self, count):
        self.count += count

class FPTree:
    def __init__(self, transactions, min_support, unwanted_tags, min_occurrences=10):
        self.unwanted_tags = set(unwanted_tags)
        self.min_occurrences = min_occurrences
        self.min_support = min_support
        self.frequent_items = self.find_frequent_items(transactions)
        self.root = FPNode(None)
        self.headers = defaultdict(lambda: None)

        for transaction in transactions:
            if isinstance(transaction, tuple):
                items, weight = transaction
            else: 
                items = transaction
                weight = 1

            filtered_items = [tag for tag in items if tag in self.frequent_items]
            ordered_items = sorted(filtered_items, key=lambda x: self.frequent_items[x], reverse=True)
            self.insert_tree(ordered_items, weight, self.root)

    def find_frequent_items(self, transactions):
        tag_counts = Counter()
        for transaction in transactions:
            if isinstance(transaction, tuple):
                tags, weight = transaction
            else: 
                tags = transaction
                weight = 1 

            for tag in set(tags):
                tag_counts[tag] += weight

        return {tag: count for tag, count in tag_counts.items() if count >= self.min_support and tag_counts[tag] >= self.min_occurrences}

    def insert_tree(self, items, weight, node):
        if items:
            first_item = items[0]
            if first_item in node.children:
                node.children[first_item].increment(weight)
            else:
                new_node = FPNode(first_item, weight)
                new_node.parent = node
                node.children[first_item] = new_node

                if self.headers[first_item] is None:
                    self.headers[first_item] = new_node
                else:
                    current = self.headers[first_item]
                    while current.link:
                        current = current.link
                    current.link = new_node
                    
            self.insert_tree(items[1:], weight, node.children[first_item])

    def mine_patterns(self, min_support):
        patterns = {}
        for item in sorted(self.frequent_items, key=lambda x: self.frequent_items[x]):
            suffix_patterns = {}
            conditional_tree_input = []
            
            node = self.headers[item]
            while node is not None:
                path = self.find_prefix_path(node)
                conditional_tree_input.extend([path] * node.count)
                node = node.link

            conditional_tree = FPTree(conditional_tree_input, min_support, self.unwanted_tags, self.min_occurrences)
            conditional_patterns = conditional_tree.mine_patterns(min_support)
            for pattern, count in conditional_patterns.items():
                suffix_patterns[pattern + (item,)] = count

            for pattern, count in suffix_patterns.items():
                patterns[pattern] = patterns.get(pattern, 0) + count
            patterns[(item,)] = self.frequent_items[item]
        
        return patterns

    def find_prefix_path(self, node):
        path = []
        while node and node.parent and node.parent.item is not None:
            node = node.parent
            path.append(node.item)
        return list(reversed(path))

def find_frequent_patterns(transactions, min_support, unwanted_tags, min_occurrences=10):
    tree = FPTree(transactions, min_support, unwanted_tags, min_occurrences)
    return tree.mine_patterns(min_support)

def process_fanfics(df, unwanted_tags, min_support, min_occurrences=10):
    transactions = [
        (set(row['tags']) - set(unwanted_tags), row['num_hits'])
        for _, row in df.iterrows()
    ]
    patterns = find_frequent_patterns(transactions, min_support, unwanted_tags, min_occurrences)
    
    sorted_patterns = sorted(patterns.items(), key=lambda x: x[1], reverse=True)[:10000]
    
    output_df = pd.DataFrame([{"Tags": ", ".join(pattern), "Weighted_Popularity": weight} for pattern, weight in sorted_patterns])
    output_df.to_csv("top_fanfic_patterns.csv", index=False)
    return output_df
