import numpy as np
import threading
import time


def get_available_resources():
    return [int(x) for x in input("Enter the values of available resources: ").split()]


def get_number_process():
    return int(input("Enter the number of processes: "))


def get_maximum_claim(num_processes):
    maximum_claim = []
    for _ in range(num_processes):
        claim = [int(x) for x in input(
            f"Enter the maximum claim for process {_}: ").split()]
        maximum_claim.append(claim)
    return maximum_claim


def get_allocation(num_processes):
    allocation = []
    for _ in range(num_processes):
        allocated = [int(x) for x in input(
            "Enter the allocation for process {}: ".format(_)).split()]
        allocation.append(allocated)
    return allocated


def get_process_id_to_request(num_processes):
    process_id = int(input(
        f"\nEnter process ID (0 to {num_processes -1 }) to request resources or -1 to exit: "))
    return process_id


def get_request():
    return np.array([int(x) for x in input("Enter requested resources: ").split()])


class BankersAlgorithm:
    def __init__(self, available, maximum, allocation):
        self.available = np.array(available)
        self.maximum = np.array(maximum)
        self.allocation = np.array(allocation)

        self.need = self.get_need()
        self.num_processes, self.num_resources = self.maximum.shape
        self.changed_info = True
        self.safe_seq = []

    def get_need(self):
        return self.maximum - self.allocation

    def release_proc_resource(self, process_id, request):
        self.allocation[process_id] -= request
        if np.any(self.allocation[process_id] < 0):
            self.allocation[process_id] += request
            print("Releasing request reject! Nothing to releaase.")
        else:
            self.need = self.get_need()
            print("Releasing Accept")
            self.print_infos()

    def request_resources(self, process_id, request):
        if not self.is_valid_request(process_id, request):
            self.changed_info = False
            print(f"Pocess {process_id}:Invalid request. Denied.")
            return

        # apply changes
        self.available -= request
        self.allocation[process_id] += request
        self.need[process_id] -= request

        if self.is_safe_state():
            print(
                f"Pocess {process_id}:Request granted. System in safe state.")
            self.changed_info = True
        else:
            #
            print(
                f"Pocess {process_id}:Request denied. Restored previous state.")
            self.changed_info = False
            self.available += request
            self.allocation[process_id] -= request
            self.need[process_id] += request

    def is_valid_request(self, process_id, request):
        # check max resouce condition
        return (request <= self.need[process_id]).all() and (request <= self.available).all()

    def is_safe_state(self):
        work = self.available.copy()
        # emtpy false array for proc
        finish = np.zeros(self.num_processes, dtype=bool)

        for _ in range(self.num_processes):
            for i in range(self.num_processes):
                # check process done yet and all resources are lower than available
                if not finish[i] and (self.need[i] <= work).all():
                    # release the allocated resources
                    work += self.allocation[i]
                    finish[i] = True           # marked as done
                    # add the process num to seq list
                    self.safe_seq.append(i)

        return finish.all()

    def print_infos(self):
        if self.changed_info:
            print("\nCurrent State:")
            print("Available resources:", self.available)
            print("Safe sequence:", self.safe_seq)

            print(
                f"{'process num' : <15}|{'max claim' : <15}|{'allocate' : <15}|{'need' : <15}")
            print(f"{'-'*15 : <15}|{'-'*15  : <15}|{'-'*15 : <15}|{'-'*15  : <15}")
            for i in range(self.num_processes):
                print(
                    f"{f'process {i}' : <15}|{str(self.maximum[i])[1:-1] : <15}|{str(self.allocation[i])[1:-1] : <15}|{str(self.need[i])[1:-1] : <15}")


class Rule:
    def __init__(self, process_id_request_or_available_resouce, request_resource, alloc_or_free=True , active = True):  # allocating
        self.process_id_request_or_available_resouce = process_id_request_or_available_resouce
        self.request_resource = request_resource
        self.alloc_or_free = alloc_or_free
        self.active = active
        self.id = None

    def info(self):
        print(f"Rule {self.id} active {self.active} info: \n")
        if self.process_id_request_or_available_resouce == -1:
            print("This rule is about availabe process!")
            if self.alloc_or_free:
                print(f"decreasing: {self.request_resource}\n")
            else:
                print(f"increasing: {self.request_resource}\n")

        else:
            print(
                f"process_id : {self.process_id_request_or_available_resouce}\n")
            if self.alloc_or_free:
                print(f"allocating: {self.request_resource}\n")
            else:
                print(f"deallocating: {self.request_resource}\n")


class DynamicResourceAllocator:
    def __init__(self, banker, interval):
        self.banker = banker
        self.interval = interval
        self.rules = []
        self.thread = None
        self.counter = 0
        self.stop_flag = False

    def register_rule(self, rule):
        rule.id = self.counter
        self.counter += 1
        self.rules.append(rule)
        print(f"Rule {rule.id} registered!")
        return rule.id

    def disable_rule(self, rule_id):
        if self.rules[rule_id]:
            self.rules[rule_id].active = False
        else:
            print("This rule is not exist!")

    def enable_rule(self, rule_id):
        if self.rules[rule_id]:
            self.rules[rule_id].active = True
        else:
            print("This rule is not exist!")

    def delete_rule(self, rule_id):
        self.rules[rule_id] = None

    def start(self):
        self.thread = threading.Thread(target=self.allocator_function)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        if self.thread is not None and self.thread.is_alive():
            self.stop_flag = True
            self.thread.join()
            print("Terminating! good bye")
  
    def get_rules_info(self):
        for rule in self.rules:
            if rule:
                rule.info()

    def allocator_function(self):
        while not self.stop_flag:
            time.sleep(self.interval)

            for rule in self.rules:
                if rule:
                    if rule.active:
                        print(f"Apply rule {rule.id}")
                        if rule.process_id_request_or_available_resouce == -1:
                            if rule.alloc_or_free:
                                self.banker.available -= rule.request_resource
                                if np.any(self.banker.available < 0):
                                    print("Decreasing available resouce reject!")
                                    self.banker.available += rule.request_resource
                                    print(self.banker.available)
                                else:
                                    print("Decreasing availabe resouces Accept")
                                    print(self.banker.available)

                            else:
                                self.banker.available += rule.request_resource
                                print("Increasing availabe resouces Accept")
                                print(self.banker.available)
                        else:
                            if rule.alloc_or_free:
                                self.banker.request_resources(
                                    rule.process_id_request_or_available_resouce, rule.request_resource)
                                self.banker.print_infos()
                            else:
                                self.banker.available += rule.request_resource
                                self.banker.release_proc_resource(
                                    rule.process_id_request_or_available_resouce, rule.request_resource)
                                self.banker.print_infos()
                    else:
                        print(f"Inactive rule {rule.id}")
                else:
                    print("No rule ")
            print("-"* 30)
def main():

    # available_resources = get_available_resources()
    # num_processes = get_number_process()
    # maximum_claim = get_maximum_claim(num_processes=num_processes)
    # allocation = get_allocation(num_processes=num_processes)

    num_processes = 5
    available_resources = [3, 3, 2]
    maximum_claim = [
        [7, 5, 3],
        [3, 2, 2],
        [9, 0, 2],
        [2, 2, 2],
        [4, 3, 3]
    ]
    allocation = [
        [0, 1, 0],
        [2, 0, 0],
        [3, 0, 2],
        [2, 1, 1],
        [0, 0, 2]
    ]

    banker = BankersAlgorithm(available_resources, maximum_claim, allocation)
    while True:

        banker.print_infos()

        process_id = get_process_id_to_request(num_processes=num_processes)
        if process_id == -1:
            break

        request = get_request()

        banker.request_resources(process_id, request)


def main_1():

    # available_resources = get_available_resources()
    # num_processes = get_number_process()
    # maximum_claim = get_maximum_claim(num_processes=num_processes)
    # allocation = get_allocation(num_processes=num_processes)

    num_processes = 5
    available_resources = [3, 3, 2]
    maximum_claim = [
        [7, 5, 3],
        [3, 2, 2],
        [9, 0, 2],
        [2, 2, 2],
        [4, 3, 3]
    ]
    allocation = [
        [0, 1, 0],
        [2, 0, 0],
        [3, 0, 2],
        [2, 1, 1],
        [0, 0, 2]
    ]

    banker = BankersAlgorithm(available_resources, maximum_claim, allocation)
    dynammic = DynamicResourceAllocator(banker , 2)
    rule0 = Rule(-1 , [1,1,0],False , False)
    rule1 = Rule(-1 , [1,1,0],True , False)
    rule2 = Rule(1 , [1,1,1],True, False)
    rule3 = Rule(1 , [2,2,2],False , False)
    rule4 = Rule(2 , [1,0,0],False, False)
    
    dynammic.start()
    time.sleep(2)
    print(dynammic.register_rule(rule0))
    print(dynammic.register_rule(rule1))
    print(dynammic.register_rule(rule2))
    print(dynammic.register_rule(rule3))
    print(dynammic.register_rule(rule4))
    dynammic.disable_rule(0)
    dynammic.disable_rule(1)
    dynammic.disable_rule(2)
    dynammic.disable_rule(3)
    dynammic.disable_rule(4)

    time.sleep(8)
    dynammic.enable_rule(0)
    # dynammic.delete_rule(0)
    time.sleep(4)
    dynammic.disable_rule(0)
    dynammic.enable_rule(1)
    
    time.sleep(4)
    dynammic.disable_rule(1)
    time.sleep(4)
    
    dynammic.enable_rule(2)
    time.sleep(8)
    dynammic.disable_rule(2)
    dynammic.enable_rule(3)
    time.sleep(4)
    dynammic.disable_rule(3)
    dynammic.banker.print_infos()
    time.sleep(4)
    dynammic.enable_rule(4)

    time.sleep(8)


    dynammic.stop()
    
    # while True:

    #     banker.print_infos()

    #     process_id = get_process_id_to_request(num_processes=num_processes)
    #     if process_id == -1:
    #         break

    #     request = get_request()

    #     banker.request_resources(process_id, request)


if __name__ == "__main__":
    # main()
    main_1()
