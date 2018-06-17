#!/usr/bin/env python

import argparse
import tensorflow as tf
import time

parser = argparse.ArgumentParser()


parser.add_argument('--checkpoint_file', required=True, metavar='checkpoint_file', help='the full path to the checkpoint file for the trained or fine-tuned model')
parser.add_argument('--Mapping_information_file_inference', required=True, metavar='file', help='a file for inference with mapping information for candidate somatic small variant sites')
parser.add_argument('--vcf_file', required=True, metavar='file', help='vcf file')
parser.add_argument('--batch_size', default=128, metavar='integer', help='total number of inference examples in a single batch')
parser.add_argument('--Candidate_somatic_sites', required=True, metavar='file', help='candidate somatic sites')

args = parser.parse_args()

def parse_example(line_batch):
    # define all values in each column to be floats
    record_defaults = [[1.0] for col in range(0, 221)]
    # use TensorFlow csv decoder to covert the string tensor into a vector representation of features 
    content = tf.decode_csv(line_batch, record_defaults = record_defaults, field_delim = '\t')
    
    # pack all features into a tensor
    features = tf.stack(content[0:221])
    # transpose the feature tensor
    features = tf.transpose(features)
    return features

def dataset_input_fn(file, batch_size = args.batch_size):
    dataset = tf.data.TextLineDataset(file)
    # combine 2805 lines into a single example
    dataset = dataset.batch(2805)
    dataset = dataset.map(parse_example)
    
    # batch multiple examples
    dataset = dataset.batch(batch_size)
    return dataset

def weight_variable(shape):
    # weight initialization, initializing weights with a small amount of noise for symmetry breaking
    # slightly positive initial bias to avoid "dead neurons" 
    initial = tf.truncated_normal(shape, stddev=0.1) # stddev: standard deviation
    return tf.Variable(initial)

def model_function(data_batch):
    input_layer = tf.reshape(data_batch, [-1, 221, 2805])
    
    # the first convolutional layer
    W_conv1 = weight_variable([3, 2805, 32])
    conv1_bn = tf.nn.conv1d(input_layer, W_conv1, stride = 1, padding='SAME')
    conv1 = tf.nn.relu(conv1_bn)
    
    # the second convolutional layer
    W_conv2 = weight_variable([3, 32, 32])
    conv2_bn = tf.nn.conv1d(conv1, W_conv2, stride = 1, padding='SAME')
    conv2 = tf.nn.relu(conv2_bn)

    # the pooling layer after the second convolutional layer
    pool2 = tf.layers.max_pooling1d(conv2, pool_size = 2, strides= 2, padding='same')

    # the third convolutional layer
    W_conv3 = weight_variable([3, 32, 64])
    conv3_bn = tf.nn.conv1d(pool2, W_conv3, stride = 1, padding='SAME')
    conv3 = tf.nn.relu(conv3_bn)
    
    # the fourth convolutional layer
    W_conv4 = weight_variable([3, 64, 64])
    conv4_bn = tf.nn.conv1d(conv3, W_conv4, stride = 1, padding='SAME')
    conv4 = tf.nn.relu(conv4_bn)

    # the pooling layer after the fourth convolutional layer
    pool4= tf.layers.max_pooling1d(conv4, pool_size = 2, strides= 2, padding='same')

    # densely connected (fully connected) layer           
    W_fc1 = weight_variable([3584, args.num_neurons_fc1])   # 56*64
    pool4_flat = tf.reshape(pool4, [-1, 3584])
    fc1_bn = tf.matmul(pool4_flat, W_fc1)
    fc1 = tf.nn.relu(fc1_bn)

    # readout layer or softmax regression
    W_fc2 = weight_variable([args.num_neurons_fc1, 2]) 
    y_conv = tf.matmul(fc1, W_fc2)
    
    # generate predictions
    prediction = tf.argmax(y_conv, axis = 1)
    probability = tf.nn.softmax(y_conv)
    return prediction, probability

def main(args):
    # create the network manually as the restored model
    inference_dataset = dataset_input_fn([args.Mapping_information_file_inference])

    # create general iterator by the from_structure() method which needs the information of output data size/shape
    iterator = tf.data.Iterator.from_structure(inference_dataset.output_types)
    data_batch = iterator.get_next()

    # make dataset that we can initialize. 
    inference_init_op = iterator.make_initializer(inference_dataset)

    # call model_function
    prediction, probability = model_function(data_batch) 
    saver = tf.train.Saver()

    with tf.Session(config = tf.ConfigProto(log_device_placement = True)) as sess:
        # restore the values of the parameters in the trained model
        saver.restore(sess, 'args.checkpoint_file')

        # set up the inference run
        start_time = time.time()
        # initialize the iterator with inference_dataset
        sess.run(inference_init_op)
        while True:
            try:
                pred, prob = sess.run([prediction, probability])
            except tf.errors.OutOfRangeError:
                break
        print('--- %s seconds ---' %(time.time() - start_time))

if __name__ == '__main__':
    main(args)