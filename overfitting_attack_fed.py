from fed_ml.Client import Clients
from fed_ml.Server import Server
from fed_ml.Attacker import Attacker


if __name__ == "__main__":
    """Set hyper-parameters."""
    epoch = 6
    learning_rate = 0.0001
    # The ml_privacy_meter can't handle the scenario with too many participants.
    CLIENT_NUMBER = 5
    # And as federated learning is online,
    # participants are uncertain about their online status in each training epoch.
    CLIENT_RATIO_PER_ROUND = 1.00
    # Some characteristics of the dataset cifar-100.
    input_shape = (32, 32, 3)
    # classes_num = 100   # cifar-100
    classes_num = 10    # cifar-10

    """Build clients and server."""
    client = Clients(input_shape=input_shape,
                    classes_num=classes_num,
                    learning_rate=learning_rate,
                    clients_num=CLIENT_NUMBER,
                     dataset_path="./datasets/cifar100.txt")
    server = Server()

    """Target the attack."""
    target_cid = 1

    """Begin training."""
    for ep in range(epoch):
        # Empty local_parameters_sum at the beginning of each epoch.
        server.initialize_local_parameters_sum()
        # Choose a random selection of active clients to train in this epoch.
        active_clients = client.choose_clients(CLIENT_RATIO_PER_ROUND)
        # Train these clients.
        for client_id in active_clients:
            client.current_cid = client_id
            print("[fed-epoch {}] cid: {}".format((ep + 1), client_id))
            # In each epoch, clients download parameters from the server,
            # and then train local models to adapt their parameters.
            client.download_global_parameters(server.global_parameters)
            # Perform passive local membership inference attack, since only get global parameters.
            if client_id == target_cid and ep == 5:
                print("overfitting attack on cid: {} in fed_ml-epoch: {}".format(client_id, (ep + 1)))
                passive_local_attacker = Attacker("Overfitting Attack", client_id, (ep + 1))
                passive_local_attacker.membership_inference_attack(client)
            if client_id == target_cid - 1:
                client.train_epoch(30)
            else:
                client.train_epoch(15)
            # Accumulate local parameters.
            current_local_parameters = client.upload_local_parameters()
            server.accumulate_local_parameters(current_local_parameters)
            
        # Update global parameters in each epoch.
        server.update_global_parameters(len(active_clients))