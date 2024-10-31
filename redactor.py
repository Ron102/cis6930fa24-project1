import sys
import os
import argparse
import glob
import re
import json
from pprint import pformat
import en_core_web_trf
import usaddress
import nltk
import transformers
from nltk.corpus import wordnet as wn
from nltk.stem import WordNetLemmatizer, PorterStemmer

nltk.download('wordnet')
nltk.download('omw-1.4')

def arg_pass():
    parser = argparse.ArgumentParser(
        description="Redact sensitive information in input files.")
    parser.add_argument("--input", action="append", required=True, type=str, help="Flag to input file pattern(s) to process. Can be specified multiple times.")
    parser.add_argument("--names", action="store_true", help="Flag to redact names.")
    parser.add_argument("--dates", action="store_true", help="Flag to redact dates. Will also redact time.")
    parser.add_argument("--phones", action="store_true", help="Flag to redact different phone number formats.")
    parser.add_argument("--address", action="store_true", help="Flag to redact addresses.")
    parser.add_argument("--concept", action="append", type=str, help="Concept words or phrases to redact.")
    parser.add_argument("--output", required=True, type=str, help="Output directory to write redacted files.",)
    parser.add_argument("--stats", required=True, type=str, help="File to write statistics. Use 'stdout' or 'stderr' to print to console, or specify file path.",)
    return parser.parse_args()

def get_synonyms(concept):
    synonyms = set()
    for syn in wn.synsets(concept):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name()) 

    stemmer = PorterStemmer()
    derivational_forms = get_derivational_forms(concept)

    all_related_words = {stemmer.stem(word) for word in synonyms.union(derivational_forms)}
    return all_related_words


def get_derivational_forms(word):
    lemmatizer = WordNetLemmatizer()
    stemmer = PorterStemmer()
    suffixes = ['ing', 'ed', 's', 'es', 'ly', 'ness', 'ment', 'tion']
    derivations = set()

    derivations.add(word)
    derivations.add(lemmatizer.lemmatize(word))
    derivations.add(stemmer.stem(word))

    for suffix in suffixes:
        derivations.add(word + suffix)
    
    return derivations

def redact_related_sentences(content, concepts, entity_counts):
    stemmer = PorterStemmer()
    
    for con in concepts:
        all_related_words = get_synonyms(con)
        count = 0
        sentences = re.split(r'(?<=[.!?])\s+', content)
        
        for j, sentence in enumerate(sentences):
            # Use stemmed words to find any derivational match in the sentence
            sentence_stems = [stemmer.stem(word) for word in sentence.split()]
            if any(word in sentence_stems for word in all_related_words):
                sentences[j] = "█" * len(sentence)
                count += 1

        content = " ".join(sentences)
        entity_counts[f"CONCEPT: {con}"] = count
        
    return content

def redact_addresses(content, entity_counts):
    tokens = content.split()
    redacted_content = []
    i = 0
    count = 0
    while i < len(tokens):
        addr_chunk = " ".join(tokens[i:i+6])
        try:
            tag_address, _ = usaddress.tag(addr_chunk)
            if 'AddressNumber' in tag_address or 'PlaceName' in tag_address:
                redacted_content.append("█" * len(addr_chunk))
                count += 1
                i += 6
                continue
        except usaddress.RepeatedLabelError:
            pass
        redacted_content.append(tokens[i])
        i += 1

    entity_counts["ADDRESS"] = count
    return " ".join(redacted_content)

def redact_content(content, nlp, label_mapping, redact_names=False, redact_dates=False, redact_phones=False, redact_address=False, concepts=None):
    mobile_pattern = r"(?:\+1\s*)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}"
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    address_pattern = r"\d+\s[A-Za-z0-9\s,]+"

    entity_counts = {}

    if concepts:
        content = redact_related_sentences(content, concepts, entity_counts)

    if redact_address:
        addresses = re.findall(address_pattern, content)
        for address in addresses:
            content = content.replace(address, "█" * len(address))
        entity_counts["ADDRESS"] = len(addresses)

    doc = nlp(content)
    entities_sorted = sorted(doc.ents, key=lambda ent: ent.start_char, reverse=True)

    for ent in entities_sorted:
        blackout_length = len(ent.text)
        blackout_text = "█" * blackout_length
        content = content[:ent.start_char] + blackout_text + content[ent.end_char:]
        if ent.label_ in label_mapping:
            entity_counts[label_mapping[ent.label_]] = entity_counts.get(label_mapping[ent.label_], 0) + 1

    if redact_phones:
        phone_nums = re.findall(mobile_pattern, content)
        for phone in phone_nums:
            content = re.sub(re.escape(phone), "█" * len(phone), content)
        entity_counts["PHONE"] = len(phone_nums)

    email_IDs = re.findall(email_pattern, content)
    for email in email_IDs:
        content = content.replace(email, "█" * len(email))
    entity_counts["EMAIL"] = len(email_IDs)

    intuitive_entity_counts = {
        label_mapping.get(key, key): value for key, value in entity_counts.items()
    }

    return content, intuitive_entity_counts

def fileprocessor(args):
    abspathsIP = [os.path.abspath(path) for path in args.input]
    abspathsOP = os.path.abspath(args.output)
    if args.stats != "stderr" and args.stats != "stdout":
        abspathsST = os.path.abspath(args.stats)

    all_file_paths = []
    for input_pattern in abspathsIP:
        file_paths = glob.glob(input_pattern)
        if not file_paths:
            sys.exit(f"No files found")
        all_file_paths.extend(file_paths)

    nlp = en_core_web_trf.load()

    label_mapping = {
        "NORP": "Nationalities or Religious or Political Groups",
        "GPE": "Geopolitical Entities",
        "FAC": "Facilities",
        "ORG": "Organizations",
        "PERSON": "Persons",
        "LOC": "Locations",
        "PRODUCT": "Products",
        "EVENT": "Events",
        "WORK_OF_ART": "Art Works",
        "LAW": "Laws",
        "LANGUAGE": "Languages",
        "DATE": "Dates",
        "TIME": "Times",
        "PERCENT": "Percentages",
        "MONEY": "Monetary Values",
        "QUANTITY": "Quantities",
        "ORDINAL": "Ordinal Numbers",
        "CARDINAL": "Cardinal Numbers",
        "PHONE": "Phone Numbers",
        "EMAIL": "Email IDs",
    }

    if os.path.exists(args.stats):
        os.remove(args.stats)

    for path in all_file_paths:
        with open(path, "r", encoding="utf-8") as file:
            content_lines = file.readlines()
            redacted_lines = []
            stats_output = {}

            for line in content_lines:
                Redacted_line, line_stats = redact_content(
                    line.strip(),
                    nlp, label_mapping,
                    redact_names=args.names,
                    redact_dates=args.dates,
                    redact_phones=args.phones,
                    redact_address=args.address,
                    concepts=args.concept
                )
                redacted_lines.append(Redacted_line)

                for key, value in line_stats.items():
                    stats_output[key] = stats_output.get(key, 0) + value

        output_path = os.path.join(args.output, os.path.basename(path) + ".censored")
        with open(output_path, "w", encoding="utf-8") as outfile:
            for redacted_line in redacted_lines:
                outfile.write(redacted_line + "\n")

        stats = pformat(stats_output)
        fileMode = "w" if not os.path.exists(args.stats) else "a"

        if args.stats == "stderr":
            sys.stderr.write(f"Filename: {os.path.basename(path)}\n")
            sys.stderr.write("Redacted Content Stats:\n")
            sys.stderr.write(stats)
            sys.stderr.write("\n\n")
        elif args.stats == "stdout":
            sys.stdout.write(f"Filename: {os.path.basename(path)}\n")
            sys.stdout.write("Redacted Content Stats:\n")
            sys.stdout.write(stats)
            sys.stdout.write("\n\n")
        else:
            with open(abspathsST, fileMode, encoding="utf-8") as statsfile:
                statsfile.write(f"Filename: {os.path.basename(path)}\n")
                statsfile.write("Redacted Content Stats:\n")
                statsfile.write(stats)
                statsfile.write("\n\n")

def main():
    args = arg_pass()
    fileprocessor(args)

if __name__ == "__main__":
    main()
