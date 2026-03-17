import random
import json
import argparse
import itertools
from pathlib import Path
from typing import List
from .classes import ConstraintProblem
NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Margaret", "Anthony", "Betty", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Dorothy", "Paul", "Kimberly", "Andrew", "Emily", "Joshua", "Donna",
    "Kenneth", "Michelle", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa",
    "Edward", "Deborah", "Ronald", "Stephanie", "Timothy", "Rebecca", "Jason", "Laura",
    "Jeffrey", "Sharon", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy",
    "Nicholas", "Shirley", "Eric", "Angela", "Jonathan", "Helen", "Stephen", "Anna",
    "Larry", "Brenda", "Justin", "Pamela", "Scott", "Nicole", "Brandon", "Emma",
    "Benjamin", "Samantha", "Samuel", "Katherine", "Gregory", "Christine", "Frank", "Debra",
    "Alexander", "Rachel", "Raymond", "Catherine", "Patrick", "Carolyn", "Jack", "Janet"
] 

TALLER_SYNONYMS = [
    'bigger',
    'taller',
    'more tall',
    'more big'
]

SHORTER_SYNONYMS = [
    'shorter',
    'more short',
    'littler',
    'more little',
    'smaller',
    'more small',
    'more petite'
]

ADVERBS = [
    'a bit',
    'slightly',
    'way',
    'a little bit',
    'much',
    'a tiny bit',
    'quite a bit',
    'just a tiny bit',
    'far',
    'just about',
    'even'
]

CONNECTIVES = [
    '.',
    ' and',
    ' but'
]

def _negate(sentence : str):
    """Simple negation function for my pre-defined sentences taller -> shorter and vice versa"""
    sentence = sentence.replace(' is ', ' is not ')
    if 'taller' in sentence:
        sentence = sentence.replace(' taller ', ' shorter ')
    elif 'shorter' in sentence:
        sentence = sentence.replace(' shorter ', ' taller ')
    return sentence

def _synonymise(sentence : str):
    """Apply appropriate synonym"""
    if 'taller' in sentence:
        sentence = sentence.replace(' taller ', f' {random.choice(TALLER_SYNONYMS)} ')
    elif 'shorter' in sentence:
        sentence = sentence.replace(' shorter ', f' {random.choice(SHORTER_SYNONYMS)} ')
    return sentence
    
def _adverbise(sentence: str):
    """Apply an adverb - must happen before synonymise"""
    if 'taller' in sentence:
        sentence = sentence.replace(' taller ', f' {random.choice(ADVERBS)} taller ')
    elif 'shorter' in sentence:
        sentence = sentence.replace(' shorter ', f' {random.choice(ADVERBS)} shorter ')
    return sentence
    

def generate_constraint_problem(
    sorted_list : List[str],
    synonyms: bool = True,
    negations: bool = True,
    connectives: bool = True,
    adverbs: bool = True
) -> ConstraintProblem:
    """
    Given the ordered list of names by height, we generate a noisy, text version to prompt the LLM with.
    Raises error if invalid sorted list
    """
    description = "Rank the following people from shortest to tallest. Output your result as a python list e.g. ['A', 'B']\n"
    sentences = []

    # Sorted_list must have at least two elements
    if len(sorted_list) < 2:
        raise ValueError("List must have at least two names")
    
    # Convert to all clean lower case string and remove non-letters
    sorted_list = [''.join(c for c in str(x).lower() if c.isascii() and c.isalpha()) for x in sorted_list]

    # Check all names are unique in the list
    if len(sorted_list) != len(set(sorted_list)):
        raise ValueError('All names must be unique')

    # ensure that all names are mentioned
    # noise, and, but, synonyms, negations
    for i in range(len(sorted_list) - 1):
        num_choices = 2
        choice = random.randint(0, num_choices - 1)
        sentence = []
        # pick random taller person
        short = sorted_list[i]
        tall = sorted_list[i + 1]
        if choice == 0:
            sentence = f"{tall} is taller than {short}"
        elif choice == 1:
            sentence = f"{short} is shorter than {tall}"
        sentences.append(sentence)

    # Apply other parameters

    # Apply negation randomly
    for i in range(len(sentences)):
        # 50% chance of applying negation to each sentence
        if negations and random.random() > 0.5:
            sentences[i] = _negate(sentences[i])

        # Apply adverbs - 70% chance of applying. don't apply adverbs with negation as this can get messy!
        # For example, X is not WAY taller than Y -> is shorter than Y OR is a little bit taller than Y
        elif adverbs and random.random() > 0.7:
            sentences[i] = _adverbise(sentences[i])

        # Apply synonyms
        if synonyms:
            sentences[i] = _synonymise(sentences[i])



    random.shuffle(sentences)
    # Apply connectives
    if not connectives: 
        description += '. '.join(sentences)
    else:
        description += sentences[0] # no connective for first sentence
        for i in range(1, len(sentences)):
            description += f"{random.choice(CONNECTIVES)} {sentences[i]}"
        
        description += "."
    

    return ConstraintProblem(input = description, golden_label = str(sorted_list))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate constraint ranking problems")
    parser.add_argument(
        "--num-samples",
        type=int,
        default=3,
        help="Number of problems to generate (default: 3)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (default: print to stdout)"
    )
    parser.add_argument(
        "--num-names",
        type=int,
        default=5,
        help="Number of names in each problem (default: 5)"
    )
    parser.add_argument(
        "--synonyms",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Replace 'taller'/'shorter' with synonyms (default: disabled)"
    )
    parser.add_argument(
        "--negations",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Randomly negate sentences (default: disabled)"
    )
    parser.add_argument(
        "--connectives",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Join sentences with connectives like 'and'/'but' (default: disabled)"
    )
    parser.add_argument(
        "--adverbs",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Insert adverbs like 'slightly'/'much' (default: disabled)"
    )
    parser.add_argument(
        "--complete-problems",
        type=int,
        default=None,
        metavar="MAX_NUM",
        help="Generate every flag combination (synonyms/negations/adverbs/connectives on or off) "
             "for each list size from 2 to MAX_NUM. MAX_NUM must be between 2 and 99 inclusive."
    )

    args = parser.parse_args()

    # Generate the requested number of problems
    examples = []

    if args.complete_problems is not None:
        # Try every combination of parameters for generating a problem
        max_num = args.complete_problems
        if max_num < 2 or max_num >= 100:
            parser.error("--complete-problems MAX_NUM must be between 2 and 99 inclusive")
        flag_names = ["synonyms", "negations", "adverbs", "connectives"]
        for n, flags in itertools.product(
            range(2, max_num + 1),
            itertools.product([True, False], repeat=len(flag_names)),
        ):
            synonyms, negations, adverbs, connectives = flags
            names = NAMES.copy()
            random.shuffle(names)
            problem = generate_constraint_problem(
                sorted_list=names[:n],
                synonyms=synonyms,
                negations=negations,
                adverbs=adverbs,
                connectives=connectives,
            )
            examples.append({
                **problem.model_dump(),
                "num_names": n,
                "flags": dict(zip(flag_names, flags)),
            })
    else:
        for _ in range(args.num_samples):
            names = NAMES.copy()
            random.shuffle(names)
            names = names[:args.num_names]
            problem = generate_constraint_problem(
                sorted_list=names,
                synonyms=args.synonyms,
                negations=args.negations,
                connectives=args.connectives,
                adverbs=args.adverbs,
            )
            examples.append(problem.model_dump())

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'a') as f:
            for example in examples:
                f.write(json.dumps(example) + "\n")
        print(f"Generated {len(examples)} problems and appended to {args.output}")
    else:
        for example in examples:
            print(json.dumps(example))
