import tensorflow as tf2
import tensorflow.compat.v1 as tf
tf.disable_eager_execution()
import numpy as np
from collections import namedtuple
import math

from Model import AlexNet
from Dataset import Dataset

# The definition of fed model, a named tuple, what an amazing idea!
FedModel = namedtuple("FedModel", "X Y DROP_RATE train_op loss_op acc_op loss prediction grads")

class Clients:
    def __init__(self, input_shape, num_classes, learning_rate, clients_num, dataset_path="../ml_privacy_meter/datasets/cifar100.txt"):
        self.graph = tf.Graph()
        tf.reset_default_graph()
        self.sess = tf.Session(graph=self.graph)

        # Call the create function to build the computational graph of AlexNet
        net = AlexNet(input_shape, num_classes, learning_rate, self.graph)
        self.model = FedModel(*net)

        # initialize
        with self.graph.as_default():
            self.sess.run(tf.global_variables_initializer())

        # Load Cifar-10 dataset
        # NOTE: len(self.dataset.train) == clients_num
        # self.dataset = Dataset(tf.keras.datasets.cifar10.load_data,
        #                 split=clients_num)
        self.dataset = Dataset(dataset_path, split=clients_num)
        # self.dataset = Dataset(tf.keras.datasets.mnist.load_data,
        #                        split=clients_num)

    def run_test(self, num):
        with self.graph.as_default():
            batch_x, batch_y = self.dataset.test.next_batch(num)
            feed_dict = {
                self.model.X: batch_x,
                self.model.Y: batch_y,
                self.model.DROP_RATE: 0
            }
        return self.sess.run([self.model.acc_op, self.model.loss_op],
                             feed_dict=feed_dict)

    def train_epoch(self, cid, batch_size=32, dropout_rate=0.5):
        """
        Train one client with its own data for one epoch.
        And we leave a back door at here.
        cid: Client id
        """
        prediction = []
        modelY = []
        loss = []
        dataset = self.dataset.train[cid]
        print(dataset.size)
        with self.graph.as_default():
            for _ in range(math.ceil(dataset.size / batch_size)):
                batch_x, batch_y = dataset.next_batch(batch_size)
                # tf.reshape(batch_x, [16, 28, 28, 2])
                feed_dict = {
                    self.model.X: batch_x,
                    self.model.Y: batch_y,
                    self.model.DROP_RATE: dropout_rate
                }
                self.sess.run(self.model.train_op, feed_dict=feed_dict)
                loss = np.hstack((loss, self.sess.run(self.model.loss, feed_dict=feed_dict)))
                grads = self.sess.run(self.model.grads, feed_dict=feed_dict)
        return prediction, modelY, loss, grads

    def get_client_vars(self):
        """ Return all of the variables list """
        with self.graph.as_default():
            client_vars = self.sess.run(tf.trainable_variables())
        return client_vars

    def set_global_vars(self, global_vars):
        """ Assign all of the variables with global vars """
        with self.graph.as_default():
            all_vars = tf.trainable_variables()
            for variable, value in zip(all_vars, global_vars):
                variable.load(value, self.sess)

    def choose_clients(self, ratio=1.0):
        """ randomly choose some clients """
        client_num = self.get_clients_num()
        choose_num = math.floor(client_num * ratio)
        return np.random.permutation(client_num)[:choose_num]

    def get_clients_num(self):
        return len(self.dataset.train)