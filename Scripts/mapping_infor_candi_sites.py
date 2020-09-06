#!/usr/bin/env python

'''Create a file with mapping information for candidate or validated somatic small variant sites and their neighbours.
'''

import argparse
import re
import itertools
import time
from xphyle import xopen

parser = argparse.ArgumentParser()

parser.add_argument('--Candidate_validated_somatic_sites', required=True, metavar='file', help='a file of candidate or validated somatic sites')
parser.add_argument('--Tumor_Normal_mpileup', required=True, metavar='pileup', help='a mixed mpileup file from tumor and normal bam files generated by samtools')
parser.add_argument('--Mapping_information_file', required=True, metavar='file', help='a file with mapping information for candidate or validated somatic small variant sites')
parser.add_argument('--indicator', default='inference', metavar='training or inference', help='creating input for the CNN model for training or inference')
parser.add_argument('--length', default=101, metavar='integer', help='read length')
parser.add_argument('--number_of_columns', required=True, type=int, help='the number of flanking genomic sites to the left or right of the candidate somatic site')

args = parser.parse_args()

def locate(source, pattern = ['\+[0-9]+', '\-[0-9]+']):
    # identify the indexes and strand information of all the indels and mismatches in the mapped reads in tumor and normal
    field_holder = source

    # remove the symbol that marks the start or end of a read segment
    field_holder = re.sub('\$', '', field_holder)
    field_holder = re.sub('\^.', '', field_holder)
    index_all = []
    strand_all = []
    state_all = []
    # identify all the indels
    mask = re.findall('[\+\-][0-9]+', field_holder)
    mask_new = [int(x[1:]) for x in mask]
    for patt in pattern:
        match = re.findall(patt, field_holder)

        # identify the insertion
        if patt[1] == '+' and len(match) > 0:
            match_new = [int(x[1:]) for x in match]
            match_set = sorted(list(set(match_new)))
            for num in match_set:
                # identify the insertion in the forward strand
                create_pattern = '\+' + str(num) + '[ACGTN]' + '{' + str(num) + '}'
                field_holder = re.sub(create_pattern, 'X', field_holder)
                
                # remove other indels
                tem_holder = field_holder
                for tem in sorted(list(set(mask_new) - set([num]))):
                    create_tem_pattern = '\+' + str(tem) + '[ACGTNacgtn]' + '{' + str(tem) + '}'
                    tem_holder = re.sub(create_tem_pattern, '', tem_holder)
                    create_tem_pattern = '\-' + str(tem) + '[ACGTNacgtn]' + '{' + str(tem) + '}'
                    tem_holder = re.sub(create_tem_pattern, '', tem_holder)
                create_tem_pattern = '\+' + str(num) + '[acgtn]' + '{' + str(num) + '}'
                tem_holder = re.sub(create_tem_pattern, '', tem_holder)
                create_tem_pattern = '\-' + str(num) + '[ACGTNacgtn]' + '{' + str(num) + '}'
                tem_holder = re.sub(create_tem_pattern, '', tem_holder)

                # identify the indexes of the specific insertion in the forward strand in the processed mapped reads
                position = [m.start() for m in re.finditer('X', tem_holder)]
                if len(position) == 0:
                    pass
                else:
                    for i in position:
                        index_all.append(i - position.index(i) - 1)
                        strand_all.append('01') # forward strand
                        state_all.append('0001') # insertion
                field_holder = re.sub('X', '', field_holder)
                
                # identify the insertion in the reverse strand
                create_pattern = '\+' + str(num) + '[acgtn]' + '{' + str(num) + '}'
                field_holder = re.sub(create_pattern, 'x', field_holder)
                
                # remove other indels
                tem_holder = field_holder
                for tem in sorted(list(set(mask_new) - set([num]))):
                    create_tem_pattern = '\+' + str(tem) + '[ACGTNacgtn]' + '{' + str(tem) + '}'
                    tem_holder = re.sub(create_tem_pattern, '', tem_holder)
                    create_tem_pattern = '\-' + str(tem) + '[ACGTNacgtn]' + '{' + str(tem) + '}'
                    tem_holder = re.sub(create_tem_pattern, '', tem_holder)
                create_tem_pattern = '\+' + str(num) + '[ACGTN]' + '{' + str(num) + '}'
                tem_holder = re.sub(create_tem_pattern, '', tem_holder)
                create_tem_pattern = '\-' + str(num) + '[ACGTNacgtn]' + '{' + str(num) + '}'
                tem_holder = re.sub(create_tem_pattern, '', tem_holder)
                
                # identify the indexes of the specific insertion in the reverse strand
                position = [m.start() for m in re.finditer('x', tem_holder)]
                if len(position) == 0:
                    pass
                else:
                    for i in position:
                        index_all.append(i - position.index(i) - 1)
                        strand_all.append('10') # reverse strand
                        state_all.append('0001') # insertion
                field_holder = re.sub('x', '', field_holder)
        
        # no indels found
        elif patt[1] == '+' and len(match) == 0:
            pass
        elif patt[1] == '-' and len(match) == 0:
            pass

        # identify the deletion
        elif patt[1] == '-' and len(match) > 0:
            match_new = [int(x[1:]) for x in match]
            match_set = sorted(list(set(match_new)))
            for num in match_set:
                # identify the deletion in the forward strand
                create_pattern = '\-' + str(num) + '[ACGTN]' + '{' + str(num) + '}'
                field_holder = re.sub(create_pattern, 'X', field_holder)
                
                # remove other indels
                tem_holder = field_holder
                for tem in sorted(list(set(mask_new) - set([num]))):
                    create_tem_pattern = '\+' + str(tem) + '[ACGTNacgtn]' + '{' + str(tem) + '}'
                    tem_holder = re.sub(create_tem_pattern, '', tem_holder)
                    create_tem_pattern = '\-' + str(tem) + '[ACGTNacgtn]' + '{' + str(tem) + '}'
                    tem_holder = re.sub(create_tem_pattern, '', tem_holder)
                create_tem_pattern = '\+' + str(num) + '[ACGTNacgtn]' + '{' + str(num) + '}'
                tem_holder = re.sub(create_tem_pattern, '', tem_holder)
                create_tem_pattern = '\-' + str(num) + '[acgtn]' + '{' + str(num) + '}'
                tem_holder = re.sub(create_tem_pattern, '', tem_holder)
                
                # identify the indexes of the specific deletion in the forward strand
                position = [m.start() for m in re.finditer('X', tem_holder)]
                if len(position) == 0:
                    pass
                else:
                    for i in position:
                        index_all.append(i - position.index(i) - 1)
                        strand_all.append('01') # forward strand
                        state_all.append('0010') # deletion
                field_holder = re.sub('X', '', field_holder)
                
                # identify the deletion in the reverse strand
                create_pattern = '\-' + str(num) + '[acgtn]' + '{' + str(num) + '}'
                field_holder = re.sub(create_pattern, 'x', field_holder)
                
                # remove other indels
                tem_holder = field_holder
                for tem in sorted(list(set(mask_new) - set([num]))):
                    create_tem_pattern = '\+' + str(tem) + '[ACGTNacgtn]' + '{' + str(tem) + '}'
                    tem_holder = re.sub(create_tem_pattern, '', tem_holder)
                    create_tem_pattern = '\-' + str(tem) + '[ACGTNacgtn]' + '{' + str(tem) + '}'
                    tem_holder = re.sub(create_tem_pattern, '', tem_holder)
                create_tem_pattern = '\+' + str(num) + '[ACGTNacgtn]' + '{' + str(num) + '}'
                tem_holder = re.sub(create_tem_pattern, '', tem_holder)
                create_tem_pattern = '\-' + str(num) + '[ACGTN]' + '{' + str(num) + '}'
                tem_holder = re.sub(create_tem_pattern, '', tem_holder)
                
                # identify the indexes of the specific deletion in the reverse strand
                position = [m.start() for m in re.finditer('x', tem_holder)]
                if len(position) == 0:
                    pass
                else:
                    for i in position:
                        index_all.append(i - position.index(i) - 1)
                        strand_all.append('10') # reverse strand
                        state_all.append('0010') # deletion
                field_holder = re.sub('x', '', field_holder)
    indel_index = index_all
    
    # identify the indexes of mismatched and matched bases
    for base in ['A', 'a', 'T', 't', 'G', 'g', 'C', 'c', 'N', 'n', '\.', ',']:
        if len(re.findall(base, field_holder)) == 0:
            pass        # no mismatched and matched bases found
        else:
            position = [m.start() for m in re.finditer(base, field_holder)]

            # check if there are indexes of matched bases followed by indels
            if len(indel_index) == 0:
                for i in position:
                    index_all.append(i)
                    if base in 'AaTtGgCcNn':
                        state_all.append('0100') # mismatch
                        if base.isupper():
                            strand_all.append('01') # forward strand
                        else:
                            strand_all.append('10') # reverse strand
                    else:
                        state_all.append('1000') # match
                        if base == '\.':
                            strand_all.append('01') # forward strand
                        else:
                            strand_all.append('10') # reverse strand
            else: 
                # keep just the indexes of mismatches or matches
                position = sorted(list(set(position) - set(indel_index)))  
                for i in position:
                    index_all.append(i)
                    if base in 'AaTtGgCcNn':
                        state_all.append('0100') # mismatch
                        if base.isupper():
                            strand_all.append('01') # forward strand
                        else:
                            strand_all.append('10') # reverse strand
                    else:
                        state_all.append('1000') # match
                        if base == '\.':
                            strand_all.append('01') # forward strand
                        else:
                            strand_all.append('10') # reverse strand

    # restrict the depth to be equal to or less than 100
    if len(index_all) <= 100:
        pass
    else:
        index_all = index_all[:100]
        strand_all = strand_all[:100]
        state_all = state_all[:100]     
    return index_all, strand_all, state_all, field_holder

def append_mapping_infor(lines, index_list, strand_all_list, state_all_list, field_holder_sample, mapping, sample):
    base = ['A', 'T', 'G', 'C', 'N']
    encoding = ['00001', '00010', '00100', '01000', '10000'] # encoding for bases
    for i in index_list:
        read_base = field_holder_sample[i]
        if read_base in '.,':
            read_base = mapping[2].upper()  # read_base is the same as reference base
        else:
            read_base = read_base.upper()   # read_base is non reference base
        
        # encoding for read base
        for rb in encoding[base.index(read_base)]:
            lines.append(rb)    
        j = index_list.index(i)
        # encoding for strand information
        for stra in strand_all_list[j]:
            lines.append(stra) 
        # encoding for state information (insertion, deletion, mismatch, match)
        for state in state_all_list[j]:
            lines.append(state) 
        
        # encoding base, mapping quality and distance to the read end in normal
        if sample == 'normal':
            bq = mapping[10][i]
            prob = 10**((33 - ord(bq))/10)
            lines.append(str(prob))   # base quality
            mq = mapping[11][i]
            prob = 10**((33 - ord(mq))/10)
            lines.append(str(prob))  # mapping quality
            dis = int(mapping[12].split(',')[i])/int(args.length)
            lines.append(str(dis))                 # distance to the read end
        
        # encoding base, mapping quality and distance to the read end in tumor
        else:
            bq = mapping[5][i]
            prob = 10**((33 - ord(bq))/10)
            lines.append(str(prob))   # base quality
            mq = mapping[6][i]
            prob = 10**((33 - ord(mq))/10)
            lines.append(str(prob))  # mapping quality
            dis = int(mapping[7].split(',')[i])/int(args.length)
            lines.append(str(dis))                 # distance to the read end 
    return lines # mapping information in one genomic site or column

def generate_mapping_infor_reads(col, holder):
    base = ['A', 'T', 'G', 'C', 'N']
    encoding = ['00001', '00010', '00100', '01000', '10000'] # encoding for bases
    lines = []
    mapping = col[1].rstrip('\n').split('\t')
    
    # the first 5 rows: encoding for base in the reference genome
    for ele in encoding[base.index(mapping[2].upper())]:
        lines.append(ele)    
    
    # max(depth) = 100, reference base takes 5 rows 
    # each read base takes 14 rows (base: 5 rows, strand: 2 rows, state: 4 rows, base_quality: 1 row, mapping quality: 1 row and distance: 1 row)
    # the number of total rows in each column is 2805 (5 + 100*14 + 100*14)
    index_all_tumor, strand_all_tumor, state_all_tumor, field_holder_tumor = locate(mapping[4])
    index_all_normal, strand_all_normal, state_all_normal, field_holder_normal = locate(mapping[9])
    
    # add information about mapped reads
    # no mapped reads in the genomic site of tumor and normal 
    if len(index_all_tumor) == 0 and len(index_all_normal) == 0:
        for i in range(5, 2805):
            lines.append('-1') # the value is -1 if no mismatches and matches and indels is in tumor and normal bases
    
    # no mapped reads in tumor
    elif len(index_all_tumor) == 0 and len(index_all_normal) > 0:
        for i in range(5, 1405):
            lines.append('-1')                 
        lines = append_mapping_infor(lines, index_all_normal, strand_all_normal, state_all_normal, field_holder_normal, mapping, 'normal')
        for pad in range(1405 + 14*len(index_all_normal), 2805):
            lines.append('-1')   # the value is '-1' for the rest rows
    
    # no mapped reads in normal
    elif len(index_all_tumor) > 0 and len(index_all_normal) == 0:
        lines = append_mapping_infor(lines, index_all_tumor, strand_all_tumor, state_all_tumor, field_holder_tumor, mapping, 'tumor')
        for pad in range(5 + 14*len(index_all_tumor), 1405):
            lines.append('-1')   # the value is '-1' for the rest rows
        for i in range(1405, 2805):
            lines.append('-1')
    else:
        # information about mapped reads in tumor
        lines = append_mapping_infor(lines, index_all_tumor, strand_all_tumor, state_all_tumor, field_holder_tumor, mapping, 'tumor')
        for pad in range(5 + 14*len(index_all_tumor), 1405):
            lines.append('-1')   # the value is '-1' for the rest rows if the depth of tumor is less than 100
        # information about mapped reads in normal
        lines = append_mapping_infor(lines, index_all_normal, strand_all_normal, state_all_normal, field_holder_normal, mapping, 'normal')
        for pad in range(1405 + 14*len(index_all_normal), 2805):
            lines.append('-1')   # the value is '-1' for the rest rows if the depth of normal is less than 100
    holder.append(lines) # buffer information of each column  
    return holder   

def main(args):
    with xopen(args.Tumor_Normal_mpileup, 'rt') as TN, open(args.Candidate_validated_somatic_sites, 'rt') as Cs, open(args.Mapping_information_file, 'wt') as Mi:
        enume_Cs = enumerate(Cs) 
        enume_TN = enumerate(TN)
        for line in enume_Cs:
            holder = []
            
            # creating input for training or inference
            if args.indicator == 'training':
                label = []
            else:
                pass

            base = ['A', 'T', 'G', 'C', 'N']
            line_content = line[1].rstrip('\n').split('\t')
            
            # encoding for bases
            encoding = ['00001', '00010', '00100', '01000', '10000'] 
            
            # process the first line
            if line[0] == 0:
                for col in itertools.islice(enume_TN, int(line_content[0]) - args.number_of_columns, int(line_content[0]) + args.number_of_columns +1):
                    holder = generate_mapping_infor_reads(col, holder) 
                keep = int(line_content[0])

                # creating input for training or inference
                if args.indicator == 'training':
                    for i in range(2805):
                        label.append(line_content[3])
                    holder.append(label)
                    overlap = holder[:-1]
                else:
                    overlap = holder

                # write to a file in row order
                for row in zip(*holder):
                    Mi.write('\t'.join(row) + '\n')
            
            # process the rest lines 
            else: 
                # the distance between two candidate or validated genomic sites 
                gap = int(line_content[0]) - keep
                
                # the distance larger than the window size of 2*n
                if gap > 2*args.number_of_columns:
                    for col in itertools.islice(enume_TN, gap - 2*args.number_of_columns -1, gap):
                        holder = generate_mapping_infor_reads(col, holder)

                    # creating input for training or inference
                    if args.indicator == 'training':
                        for i in range(2805):
                            label.append(line_content[3])
                        holder.append(label)
                        overlap = holder[:-1]
                    else:
                        overlap = holder

                    for row in zip(*holder):
                        Mi.write('\t'.join(row) + '\n')
                    keep = int(line_content[0])
                
                # the distance smaller than the window size of 2*n
                else:
                    # copy the information of overlapping window from last column
                    for infor in overlap[gap:]:
                        holder.append(infor)
                    overlap = []
                    for col in itertools.islice(enume_TN, 0, gap):
                        holder = generate_mapping_infor_reads(col, holder)

                    # creating input for training or inference
                    if args.indicator == 'training':
                        for i in range(2805):
                            label.append(line_content[3])
                        holder.append(label)
                        overlap = holder[:-1]
                    else:
                        overlap = holder

                    for row in zip(*holder):
                        Mi.write('\t'.join(row) + '\n')
                    keep = int(line_content[0])

if __name__ == '__main__':
    start_time = time.time()
    main(args)
    print('--- %s seconds ---' %(time.time() - start_time))